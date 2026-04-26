"""
Paragraph Extractor

Extracts complex legal paragraphs from raw BDDK documents.
Filters by length, jargon density, and structural quality
to build the source side of the parallel simplification dataset.
"""

import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Optional

import yaml
import jsonlines

sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Turkish banking / legal jargon terms for complexity detection
BANKING_JARGON = {
    "sermaye", "yeterlilik", "likidite", "mevduat", "teminat", "kredi",
    "konsolidasyon", "faiz", "döviz", "varlık", "yükümlülük", "karşılık",
    "ihtiyat", "temerrüt", "tahakkuk", "amortisman", "itfa", "provizyon",
    "münhasıran", "müteselsil", "müteakip", "muaccel", "munzam",
    "tedavül", "tasarruf", "temlik", "devir", "iktisap", "tasfiye",
    "hükmi", "tüzel", "ticari", "mali", "nakdi", "gayri nakdi",
    "repo", "ters repo", "swap", "opsiyon", "türev", "menkul kıymet",
    "tahvil", "bono", "hisse senedi", "ipotek", "rehin", "haciz",
    "iflas", "konkordato", "alacak", "borç", "bilanço", "hesap",
    "risk", "denetim", "teftiş", "yönetmelik", "tebliğ", "genelge",
    "kanun", "madde", "fıkra", "bent", "hüküm", "mevzuat",
    "düzenleme", "yaptırım", "idari para cezası", "müeyyide",
    "banka", "finans", "sigorta", "reasürans", "aktüer",
    "konsolide", "bireysel", "kurumsal", "perakende", "toptan",
    "kredi riski", "piyasa riski", "operasyonel risk",
    "özkaynak", "sermaye tamponu", "kaldıraç oranı",
    "sorunlu alacak", "takipteki alacak", "donuk alacak",
    "BDDK", "TCMB", "SPK", "TMSF", "TBB",
}

# Complex sentence indicators (subordination, formal register)
COMPLEXITY_MARKERS = [
    r"\b(?:şu kadar ki|ancak|bununla birlikte|nitekim)\b",
    r"\b(?:hükmünde|kapsamında|çerçevesinde|uyarınca|gereğince)\b",
    r"\b(?:halinde|durumunda|koşuluyla|şartıyla|kaydıyla)\b",
    r"\b(?:itibaren|itibariyle|bakımından|açısından)\b",
    r"\b(?:aşağıdaki|yukarıdaki|işbu|mezkur|bahsi geçen)\b",
    r"\b(?:münhasıran|müstakilen|müştereken|müteselsilen)\b",
]


def compute_jargon_density(text: str) -> float:
    """
    Compute the ratio of banking/legal jargon words in the text.
    
    Args:
        text: Input text
        
    Returns:
        Ratio of jargon words to total words (0.0 - 1.0)
    """
    words = text.lower().split()
    if not words:
        return 0.0
    
    jargon_count = sum(1 for w in words if w in BANKING_JARGON)
    
    # Also check multi-word jargon
    text_lower = text.lower()
    for term in BANKING_JARGON:
        if " " in term and term in text_lower:
            jargon_count += 1
    
    return jargon_count / len(words)


def compute_complexity_score(text: str) -> float:
    """
    Compute a complexity score based on structural indicators.
    Higher score = more complex text.
    
    Args:
        text: Input text
        
    Returns:
        Complexity score (0.0+)
    """
    score = 0.0
    
    # Check for complexity markers
    for pattern in COMPLEXITY_MARKERS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        score += len(matches) * 0.5
    
    # Average sentence length (longer = more complex)
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if sentences:
        avg_sentence_len = sum(len(s.split()) for s in sentences) / len(sentences)
        if avg_sentence_len > 25:
            score += 1.0
        if avg_sentence_len > 40:
            score += 1.0
    
    # Subordinate clause depth (commas as proxy)
    comma_count = text.count(",")
    if comma_count > 5:
        score += 0.5
    
    # Parenthetical expressions
    paren_count = text.count("(")
    score += paren_count * 0.3
    
    return score


def extract_paragraphs_from_markdown(
    content: str,
    doc_id: str,
    min_length: int = 100,
    max_length: int = 2000,
    min_jargon_density: float = 0.02,
) -> list[dict]:
    """
    Extract complex legal paragraphs from a Markdown document.
    
    Args:
        content: Raw Markdown content
        doc_id: Source document identifier
        min_length: Minimum paragraph length in characters
        max_length: Maximum paragraph length in characters
        min_jargon_density: Minimum jargon density threshold
        
    Returns:
        List of paragraph dictionaries
    """
    paragraphs = []
    
    # Split into paragraphs (double newline or markdown headers)
    raw_paragraphs = re.split(r"\n\s*\n|\n#{1,6}\s", content)
    
    for idx, para in enumerate(raw_paragraphs):
        # Clean up the paragraph
        para = para.strip()
        para = re.sub(r"\s+", " ", para)  # Normalize whitespace
        para = re.sub(r"\*\*|__|##|#", "", para)  # Remove markdown formatting
        para = para.strip()
        
        # Length filter
        if len(para) < min_length or len(para) > max_length:
            continue
        
        # Skip tables, lists, and non-prose content
        if para.startswith("|") or para.startswith("-") or para.startswith("*"):
            continue
        
        # Skip paragraphs that are mostly numbers or URLs
        word_count = len(para.split())
        if word_count < 10:
            continue
        
        # Compute metrics
        jargon_density = compute_jargon_density(para)
        complexity_score = compute_complexity_score(para)
        
        # Filter by jargon density
        if jargon_density < min_jargon_density:
            continue
        
        # Create paragraph entry
        paragraph = {
            "id": f"{doc_id}_p{idx}",
            "source_doc": doc_id,
            "complex_text": para,
            "metadata": {
                "char_length": len(para),
                "word_count": word_count,
                "jargon_density": round(jargon_density, 4),
                "complexity_score": round(complexity_score, 2),
                "paragraph_index": idx,
            }
        }
        
        paragraphs.append(paragraph)
    
    return paragraphs


def process_all_documents(
    input_dir: str = "data/raw",
    output_file: str = "data/paragraphs/complex_paragraphs.jsonl",
    min_length: int = 100,
    max_length: int = 2000,
    min_jargon_density: float = 0.02,
) -> dict:
    """
    Process all raw BDDK documents and extract complex paragraphs.
    
    Args:
        input_dir: Directory containing raw Markdown documents
        output_file: Output JSONL file path
        min_length: Minimum paragraph length
        max_length: Maximum paragraph length
        min_jargon_density: Minimum jargon density
        
    Returns:
        Processing statistics
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    stats = {
        "documents_processed": 0,
        "total_paragraphs": 0,
        "filtered_paragraphs": 0,
        "avg_complexity": 0.0,
        "avg_jargon_density": 0.0,
    }
    
    all_paragraphs = []
    complexity_scores = []
    jargon_densities = []
    
    # Process each markdown file
    md_files = sorted(Path(input_dir).glob("bddk_*.md"))
    
    if not md_files:
        logger.warning(f"No BDDK documents found in {input_dir}")
        return stats
    
    logger.info(f"Processing {len(md_files)} documents from {input_dir}")
    
    for md_file in md_files:
        doc_id = md_file.stem  # e.g., "bddk_310"
        
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        paragraphs = extract_paragraphs_from_markdown(
            content=content,
            doc_id=doc_id,
            min_length=min_length,
            max_length=max_length,
            min_jargon_density=min_jargon_density,
        )
        
        all_paragraphs.extend(paragraphs)
        
        for p in paragraphs:
            complexity_scores.append(p["metadata"]["complexity_score"])
            jargon_densities.append(p["metadata"]["jargon_density"])
        
        stats["documents_processed"] += 1
        
        if paragraphs:
            logger.info(
                f"  {doc_id}: {len(paragraphs)} paragraphs extracted"
            )
    
    # Sort by complexity score (most complex first)
    all_paragraphs.sort(
        key=lambda x: x["metadata"]["complexity_score"],
        reverse=True
    )
    
    # Write output
    with jsonlines.open(output_file, mode="w") as writer:
        for para in all_paragraphs:
            writer.write(para)
    
    # Update stats
    stats["total_paragraphs"] = len(all_paragraphs)
    if complexity_scores:
        stats["avg_complexity"] = round(
            sum(complexity_scores) / len(complexity_scores), 2
        )
    if jargon_densities:
        stats["avg_jargon_density"] = round(
            sum(jargon_densities) / len(jargon_densities), 4
        )
    
    # Save stats
    stats_file = output_file.replace(".jsonl", "_stats.json")
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    logger.info(
        f"\n📊 Extraction complete:\n"
        f"   Documents processed: {stats['documents_processed']}\n"
        f"   Paragraphs extracted: {stats['total_paragraphs']}\n"
        f"   Avg complexity score: {stats['avg_complexity']}\n"
        f"   Avg jargon density: {stats['avg_jargon_density']}\n"
        f"   Output: {output_file}"
    )
    
    return stats


def main():
    """CLI entry point for paragraph extraction."""
    parser = argparse.ArgumentParser(
        description="Extract complex legal paragraphs from BDDK documents"
    )
    parser.add_argument(
        "--config", default="configs/default.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--input-dir", default=None,
        help="Override input directory"
    )
    parser.add_argument(
        "--output-file", default=None,
        help="Override output file path"
    )
    
    args = parser.parse_args()
    
    config = yaml.safe_load(open(args.config, encoding="utf-8"))
    para_config = config["data_collection"]["paragraph_extraction"]
    
    process_all_documents(
        input_dir=args.input_dir or config["data_collection"]["bddk"]["raw_output_dir"],
        output_file=args.output_file or para_config["output_file"],
        min_length=para_config["min_paragraph_length"],
        max_length=para_config["max_paragraph_length"],
        min_jargon_density=para_config["min_jargon_density"],
    )


if __name__ == "__main__":
    main()
