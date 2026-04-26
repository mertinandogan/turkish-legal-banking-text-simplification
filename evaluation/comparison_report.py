"""
Comparison Report Generator

Aggregates all evaluation results (baselines, neural, zero-shot)
and generates a comprehensive Markdown comparison report.
"""

import argparse, json, logging, os, sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def load_json(path: str) -> dict:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def generate_report(results_dir="results", output_file="results/comparison_report.md"):
    """Generate comprehensive comparison report."""
    baseline = load_json(os.path.join(results_dir, "baseline_scores.json"))
    neural = load_json(os.path.join(results_dir, "neural_scores.json"))
    zeroshot = load_json(os.path.join(results_dir, "zeroshot_scores.json"))
    hallucination = load_json(os.path.join(results_dir, "hallucination_analysis.json"))
    faithfulness = load_json(os.path.join(results_dir, "faithfulness_analysis.json"))

    report = []
    report.append("# Turkish Legal Banking Text Simplification — Comparison Report")
    report.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    report.append("---\n")

    # Metrics table
    report.append("## Model Comparison\n")
    report.append("| Model | ROUGE-1 | ROUGE-2 | ROUGE-L | BLEU |")
    report.append("|-------|---------|---------|---------|------|")

    models = []
    if "textrank" in baseline:
        m = baseline["textrank"]["metrics"]
        models.append(("TextRank (Baseline)", m))
    if "tfidf" in baseline:
        m = baseline["tfidf"]["metrics"]
        models.append(("TF-IDF (Baseline)", m))
    if neural and "metrics" in neural:
        models.append(("Neural (mT5 + LoRA)", neural["metrics"]))
    if zeroshot and "metrics" in zeroshot:
        models.append(("Zero-Shot LLM", zeroshot["metrics"]))

    for name, m in models:
        report.append(
            f"| {name} | {m.get('rouge1', 'N/A')} | {m.get('rouge2', 'N/A')} | "
            f"{m.get('rougeL', 'N/A')} | {m.get('bleu', 'N/A')} |"
        )

    # Error analysis
    if hallucination or faithfulness:
        report.append("\n---\n")
        report.append("## Error Analysis\n")

        if hallucination:
            report.append("### Hallucination Detection\n")
            report.append(f"- **Average Hallucination Score:** {hallucination.get('avg_hallucination_score', 'N/A')}")
            report.append(f"- **Number Hallucinations:** {hallucination.get('samples_with_number_hallucination', 'N/A')} samples")
            report.append(f"- **Term Preservation Rate:** {hallucination.get('avg_term_preservation', 'N/A')}")
            report.append(f"- **Word Overlap:** {hallucination.get('avg_word_overlap', 'N/A')}\n")

        if faithfulness:
            report.append("### Faithfulness Analysis\n")
            report.append(f"- **Average Faithfulness Score:** {faithfulness.get('avg_faithfulness_score', 'N/A')}")
            report.append(f"- **TF-IDF Similarity:** {faithfulness.get('avg_tfidf_similarity', 'N/A')}")
            report.append(f"- **Low Faithfulness Count:** {faithfulness.get('low_faithfulness_count', 'N/A')} samples\n")

    # Sample predictions
    if neural and "predictions" in neural:
        report.append("---\n")
        report.append("## Sample Predictions (Neural Model)\n")
        for i, pred in enumerate(neural["predictions"][:3], 1):
            report.append(f"### Example {i}\n")
            report.append(f"**Karmaşık:** {pred.get('complex', '')}\n")
            report.append(f"**Referans:** {pred.get('reference', '')}\n")
            report.append(f"**Tahmin:** {pred.get('prediction', '')}\n")

    # Write report
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(report))

    logger.info(f"Report generated: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Generate comparison report")
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--output", default="results/comparison_report.md")
    args = parser.parse_args()
    generate_report(args.results_dir, args.output)

if __name__ == "__main__":
    main()
