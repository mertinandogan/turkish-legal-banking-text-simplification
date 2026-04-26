"""
Baseline Evaluation

Evaluates TextRank and TF-IDF extractive summarization baselines
on the parallel dataset using ROUGE and BLEU metrics.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import jsonlines
import yaml
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.baseline.textrank_summarizer import TextRankSummarizer
from models.baseline.tfidf_summarizer import TfidfSummarizer

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def compute_rouge_scores(predictions: list[str], references: list[str]) -> dict:
    """
    Compute ROUGE-1, ROUGE-2, and ROUGE-L scores.
    
    Args:
        predictions: Generated summaries
        references: Reference summaries
        
    Returns:
        Dictionary with ROUGE scores
    """
    from rouge_score import rouge_scorer
    
    scorer = rouge_scorer.RougeScorer(
        ["rouge1", "rouge2", "rougeL"],
        use_stemmer=False,  # No stemmer for Turkish
    )
    
    scores = {"rouge1": [], "rouge2": [], "rougeL": []}
    
    for pred, ref in zip(predictions, references):
        result = scorer.score(ref, pred)
        for key in scores:
            scores[key].append(result[key].fmeasure)
    
    # Average scores
    return {
        key: round(sum(vals) / len(vals), 4) if vals else 0.0
        for key, vals in scores.items()
    }


def compute_bleu_score(predictions: list[str], references: list[str]) -> float:
    """
    Compute corpus-level BLEU score.
    
    Args:
        predictions: Generated summaries
        references: Reference summaries
        
    Returns:
        BLEU score
    """
    import nltk
    from nltk.translate.bleu_score import corpus_bleu, SmoothingFunction
    
    # Ensure NLTK data is available
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt", quiet=True)
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        nltk.download("punkt_tab", quiet=True)
    
    # Tokenize
    hypotheses = [pred.split() for pred in predictions]
    refs = [[ref.split()] for ref in references]
    
    # Compute BLEU with smoothing
    smoothie = SmoothingFunction().method1
    try:
        score = corpus_bleu(refs, hypotheses, smoothing_function=smoothie)
    except (ZeroDivisionError, ValueError):
        score = 0.0
    
    return round(score, 4)


def evaluate_baseline(
    model_name: str,
    summarizer,
    test_data: list[dict],
) -> dict:
    """
    Evaluate a baseline summarizer on test data.
    
    Args:
        model_name: Name of the model
        summarizer: Summarizer instance with .summarize() method
        test_data: List of dicts with 'complex' and 'simple' keys
        
    Returns:
        Evaluation results
    """
    predictions = []
    references = []
    
    for item in tqdm(test_data, desc=f"Evaluating {model_name}"):
        summary = summarizer.summarize(item["complex"])
        predictions.append(summary)
        references.append(item["simple"])
    
    # Compute metrics
    rouge_scores = compute_rouge_scores(predictions, references)
    bleu_score = compute_bleu_score(predictions, references)
    
    # Compute length statistics
    avg_pred_len = sum(len(p) for p in predictions) / len(predictions) if predictions else 0
    avg_ref_len = sum(len(r) for r in references) / len(references) if references else 0
    
    results = {
        "model": model_name,
        "metrics": {
            **rouge_scores,
            "bleu": bleu_score,
        },
        "statistics": {
            "num_samples": len(test_data),
            "avg_prediction_length": round(avg_pred_len, 1),
            "avg_reference_length": round(avg_ref_len, 1),
            "length_ratio": round(avg_pred_len / avg_ref_len, 3) if avg_ref_len > 0 else 0,
        },
        "predictions": predictions[:5],  # Save first 5 for inspection
    }
    
    return results


def run_all_baselines(
    test_file: str = "data/parallel/test_gold.jsonl",
    output_file: str = "results/baseline_scores.json",
    config_path: str = "configs/default.yaml",
) -> dict:
    """
    Run all baseline models and save results.
    
    Args:
        test_file: Path to test dataset
        output_file: Path to save results
        config_path: Configuration file path
        
    Returns:
        Combined results
    """
    # Load config
    config = yaml.safe_load(open(config_path, encoding="utf-8"))
    baseline_config = config["models"]["baseline"]
    
    # Load test data
    test_data = []
    with jsonlines.open(test_file) as reader:
        for item in reader:
            test_data.append(item)
    
    if not test_data:
        logger.error(f"No test data found in {test_file}")
        return {}
    
    logger.info(f"Loaded {len(test_data)} test samples from {test_file}")
    
    results = {}
    
    # TextRank
    logger.info("=" * 50)
    logger.info("Evaluating TextRank...")
    textrank = TextRankSummarizer(
        num_sentences=baseline_config["textrank"]["num_sentences"],
    )
    results["textrank"] = evaluate_baseline("TextRank", textrank, test_data)
    
    logger.info(
        f"TextRank Results: "
        f"ROUGE-1={results['textrank']['metrics']['rouge1']:.4f}, "
        f"ROUGE-2={results['textrank']['metrics']['rouge2']:.4f}, "
        f"ROUGE-L={results['textrank']['metrics']['rougeL']:.4f}, "
        f"BLEU={results['textrank']['metrics']['bleu']:.4f}"
    )
    
    # TF-IDF
    logger.info("=" * 50)
    logger.info("Evaluating TF-IDF...")
    tfidf = TfidfSummarizer(
        num_sentences=baseline_config["tfidf"]["num_sentences"],
        max_features=baseline_config["tfidf"]["max_features"],
    )
    results["tfidf"] = evaluate_baseline("TF-IDF", tfidf, test_data)
    
    logger.info(
        f"TF-IDF Results: "
        f"ROUGE-1={results['tfidf']['metrics']['rouge1']:.4f}, "
        f"ROUGE-2={results['tfidf']['metrics']['rouge2']:.4f}, "
        f"ROUGE-L={results['tfidf']['metrics']['rougeL']:.4f}, "
        f"BLEU={results['tfidf']['metrics']['bleu']:.4f}"
    )
    
    # Save results
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n📊 Results saved to {output_file}")
    
    return results


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Evaluate baseline summarization models"
    )
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--test-file", default="data/parallel/test_gold.jsonl")
    parser.add_argument("--output", default="results/baseline_scores.json")
    
    args = parser.parse_args()
    
    run_all_baselines(
        test_file=args.test_file,
        output_file=args.output,
        config_path=args.config,
    )


if __name__ == "__main__":
    main()
