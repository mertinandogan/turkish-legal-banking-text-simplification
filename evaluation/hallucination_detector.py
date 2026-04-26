"""
Hallucination Detector

Detects hallucinated content in generated simplifications by checking
whether the output introduces information not present in the source.
"""

import argparse, json, logging, os, re, sys
from pathlib import Path
from typing import Optional
import jsonlines

sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Critical banking terms that MUST be preserved
CRITICAL_TERMS = [
    "sermaye yeterliliği", "likidite", "kredi riski", "piyasa riski", "operasyonel risk",
    "özkaynak", "konsolide", "bilanço", "teminat", "karşılık", "mevduat",
    "faiz oranı", "döviz kuru", "risk ağırlıklı", "kaldıraç oranı",
    "takipteki alacak", "donuk alacak", "sorunlu alacak", "ipotek", "rehin",
    "BDDK", "TCMB", "SPK", "TMSF", "yönetmelik", "tebliğ", "kanun",
]


def extract_numbers(text: str) -> set[str]:
    """Extract all numbers (amounts, percentages, dates) from text."""
    patterns = [
        r"\d+[.,]\d+",      # Decimals
        r"%\s*\d+",          # Percentages
        r"\d{1,2}\.\d{1,2}\.\d{4}",  # Dates
        r"\b\d{4,}\b",      # Large numbers (IDs, amounts)
    ]
    numbers = set()
    for p in patterns:
        numbers.update(re.findall(p, text))
    return numbers


def check_number_hallucination(source: str, generated: str) -> dict:
    """Check if generated text introduces numbers not in source."""
    src_nums = extract_numbers(source)
    gen_nums = extract_numbers(generated)
    hallucinated = gen_nums - src_nums
    return {
        "hallucinated_numbers": list(hallucinated),
        "has_number_hallucination": len(hallucinated) > 0,
        "count": len(hallucinated),
    }


def check_term_preservation(source: str, generated: str) -> dict:
    """Check if critical banking terms are preserved."""
    source_lower = source.lower()
    gen_lower = generated.lower()
    
    present_in_source = [t for t in CRITICAL_TERMS if t.lower() in source_lower]
    preserved = [t for t in present_in_source if t.lower() in gen_lower]
    missing = [t for t in present_in_source if t.lower() not in gen_lower]
    
    preservation_rate = len(preserved) / len(present_in_source) if present_in_source else 1.0
    return {
        "terms_in_source": present_in_source,
        "preserved": preserved,
        "missing": missing,
        "preservation_rate": round(preservation_rate, 4),
    }


def compute_word_overlap(source: str, generated: str) -> float:
    """Compute word-level overlap between source and generated text."""
    src_words = set(source.lower().split())
    gen_words = set(generated.lower().split())
    if not gen_words:
        return 0.0
    overlap = src_words & gen_words
    return len(overlap) / len(gen_words)


def detect_hallucinations(source: str, generated: str) -> dict:
    """Run all hallucination detection checks."""
    num_check = check_number_hallucination(source, generated)
    term_check = check_term_preservation(source, generated)
    overlap = compute_word_overlap(source, generated)
    
    # Overall hallucination score (0=no hallucination, 1=severe)
    score = 0.0
    if num_check["has_number_hallucination"]:
        score += 0.3 * min(num_check["count"], 3) / 3
    score += (1.0 - term_check["preservation_rate"]) * 0.4
    if overlap < 0.3:
        score += 0.3
    
    return {
        "hallucination_score": round(min(score, 1.0), 4),
        "number_check": num_check,
        "term_preservation": term_check,
        "word_overlap": round(overlap, 4),
    }


def analyze_dataset(input_file: str, output_file: str = "results/hallucination_analysis.json"):
    """Analyze hallucinations across a dataset of predictions."""
    data = list(jsonlines.open(input_file))
    
    results = []
    total_score = 0
    
    for item in data:
        source = item.get("complex", "")
        generated = item.get("neural_simple", item.get("simple", ""))
        analysis = detect_hallucinations(source, generated)
        analysis["id"] = item.get("id", "unknown")
        results.append(analysis)
        total_score += analysis["hallucination_score"]
    
    summary = {
        "total_samples": len(results),
        "avg_hallucination_score": round(total_score / max(len(results), 1), 4),
        "samples_with_number_hallucination": sum(1 for r in results if r["number_check"]["has_number_hallucination"]),
        "avg_term_preservation": round(
            sum(r["term_preservation"]["preservation_rate"] for r in results) / max(len(results), 1), 4),
        "avg_word_overlap": round(sum(r["word_overlap"] for r in results) / max(len(results), 1), 4),
        "details": results[:10],  # First 10 for inspection
    }
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Hallucination analysis: avg_score={summary['avg_hallucination_score']:.4f} → {output_file}")
    return summary


def main():
    parser = argparse.ArgumentParser(description="Detect hallucinations in generated text")
    parser.add_argument("--input", required=True, help="JSONL file with predictions")
    parser.add_argument("--output", default="results/hallucination_analysis.json")
    args = parser.parse_args()
    analyze_dataset(args.input, args.output)

if __name__ == "__main__":
    main()
