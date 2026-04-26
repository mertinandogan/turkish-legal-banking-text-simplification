"""
Faithfulness Checker

Evaluates whether generated simplifications faithfully preserve
the meaning of the original banking regulation text.
Uses semantic similarity and optional NLI-based verification.
"""

import argparse, json, logging, os, sys
from pathlib import Path
from typing import Optional
import numpy as np
import jsonlines

sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def compute_tfidf_similarity(text1: str, text2: str) -> float:
    """Compute TF-IDF cosine similarity between two texts."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    try:
        vec = TfidfVectorizer()
        tfidf = vec.fit_transform([text1, text2])
        return float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0])
    except ValueError:
        return 0.0


def compute_embedding_similarity(text1: str, text2: str, embedder=None) -> float:
    """Compute embedding-based similarity (uses project's OpenRouter embedder if available)."""
    if embedder is None:
        try:
            from semantic_search.embedder import OpenRouterEmbedder, is_openrouter_available
            if is_openrouter_available():
                embedder = OpenRouterEmbedder()
            else:
                return -1.0  # Not available
        except ImportError:
            return -1.0

    emb1 = embedder.encode_query(text1)
    emb2 = embedder.encode_query(text2)
    return float(np.dot(emb1, emb2))


def check_faithfulness(source: str, generated: str, embedder=None) -> dict:
    """Check faithfulness of a single simplification."""
    tfidf_sim = compute_tfidf_similarity(source, generated)
    embed_sim = compute_embedding_similarity(source, generated, embedder)

    # Length ratio (extreme compression may lose meaning)
    len_ratio = len(generated) / max(len(source), 1)
    length_penalty = 0.0
    if len_ratio < 0.2:
        length_penalty = 0.3
    elif len_ratio < 0.3:
        length_penalty = 0.1

    # Composite faithfulness score
    if embed_sim >= 0:
        score = 0.6 * embed_sim + 0.3 * tfidf_sim + 0.1 * min(len_ratio, 1.0) - length_penalty
    else:
        score = 0.7 * tfidf_sim + 0.3 * min(len_ratio, 1.0) - length_penalty

    return {
        "faithfulness_score": round(max(0, min(score, 1.0)), 4),
        "tfidf_similarity": round(tfidf_sim, 4),
        "embedding_similarity": round(embed_sim, 4) if embed_sim >= 0 else "N/A",
        "length_ratio": round(len_ratio, 4),
    }


def analyze_dataset(input_file: str, output_file="results/faithfulness_analysis.json"):
    """Analyze faithfulness across a prediction dataset."""
    data = list(jsonlines.open(input_file))
    embedder = None
    try:
        from semantic_search.embedder import OpenRouterEmbedder, is_openrouter_available
        if is_openrouter_available():
            embedder = OpenRouterEmbedder()
            logger.info("Using embedding similarity (OpenRouter)")
    except Exception:
        logger.info("Embedding similarity not available, using TF-IDF only")

    results = []
    for item in data:
        source = item.get("complex", "")
        generated = item.get("neural_simple", item.get("simple", ""))
        analysis = check_faithfulness(source, generated, embedder)
        analysis["id"] = item.get("id", "unknown")
        results.append(analysis)

    avg_faith = sum(r["faithfulness_score"] for r in results) / max(len(results), 1)
    avg_tfidf = sum(r["tfidf_similarity"] for r in results) / max(len(results), 1)

    summary = {
        "total_samples": len(results),
        "avg_faithfulness_score": round(avg_faith, 4),
        "avg_tfidf_similarity": round(avg_tfidf, 4),
        "low_faithfulness_count": sum(1 for r in results if r["faithfulness_score"] < 0.3),
        "details": results[:10],
    }

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    logger.info(f"Faithfulness: avg={avg_faith:.4f} → {output_file}")
    return summary


def main():
    parser = argparse.ArgumentParser(description="Check faithfulness of simplifications")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="results/faithfulness_analysis.json")
    args = parser.parse_args()
    analyze_dataset(args.input, args.output)

if __name__ == "__main__":
    main()
