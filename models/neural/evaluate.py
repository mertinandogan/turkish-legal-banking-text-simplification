"""
Neural Model Evaluation

Evaluates the fine-tuned model on test set using ROUGE and BLEU.
"""

import argparse, json, logging, os, sys
from pathlib import Path
import yaml, jsonlines
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from models.neural.config import ModelConfig
from models.neural.inference import NeuralSimplifier

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def evaluate_neural(config, model_path, test_file, output_file="results/neural_scores.json"):
    from models.baseline.evaluate_baselines import compute_rouge_scores, compute_bleu_score

    simplifier = NeuralSimplifier(model_path=model_path, base_model_name=config.model_name, config=config)
    data = list(jsonlines.open(test_file))
    logger.info(f"Evaluating on {len(data)} test samples")

    predictions, references = [], []
    for item in tqdm(data, desc="Neural inference"):
        pred = simplifier.simplify(item["complex"])
        predictions.append(pred)
        references.append(item["simple"])

    rouge = compute_rouge_scores(predictions, references)
    bleu = compute_bleu_score(predictions, references)

    results = {
        "model": f"neural_{config.model_name}",
        "metrics": {**rouge, "bleu": bleu},
        "statistics": {
            "num_samples": len(data),
            "avg_pred_len": round(sum(len(p) for p in predictions) / len(predictions), 1),
            "avg_ref_len": round(sum(len(r) for r in references) / len(references), 1),
        },
        "predictions": [{"complex": d["complex"][:200], "reference": d["simple"][:200],
                         "prediction": p[:200]} for d, p in zip(data[:5], predictions[:5])],
    }

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    logger.info(f"ROUGE-1={rouge['rouge1']:.4f} ROUGE-2={rouge['rouge2']:.4f} "
                f"ROUGE-L={rouge['rougeL']:.4f} BLEU={bleu:.4f}")
    logger.info(f"Results saved to {output_file}")
    return results


def main():
    parser = argparse.ArgumentParser(description="Evaluate neural simplification model")
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--model-path", default="results/neural_checkpoints/best_model")
    parser.add_argument("--test-file", default="data/parallel/test_gold.jsonl")
    parser.add_argument("--output", default="results/neural_scores.json")
    args = parser.parse_args()

    cfg = ModelConfig.from_yaml(yaml.safe_load(open(args.config, encoding="utf-8")))
    evaluate_neural(cfg, args.model_path, args.test_file, args.output)

if __name__ == "__main__":
    main()
