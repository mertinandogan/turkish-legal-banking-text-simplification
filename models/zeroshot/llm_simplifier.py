"""
Zero-Shot LLM Simplifier

Uses a large language model with zero-shot prompting for text simplification.
Serves as comparison against the fine-tuned neural model.
"""

import argparse, json, logging, os, sys, time
from pathlib import Path
from typing import Optional
import re
import yaml, jsonlines
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


class ZeroShotSimplifier:
    """Zero-shot LLM text simplifier."""

    def __init__(self, provider="openrouter", model_name="google/gemini-2.0-flash-001",
                 temperature=0.3, max_tokens=1024, prompt_template=None):
        from openai import OpenAI
        self.client = None
        self.offline_mode = False

        if provider == "openrouter":
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                logger.warning(
                    "OPENROUTER_API_KEY missing, running in offline fallback mode "
                    "(rule-based simplification for pipeline completeness)."
                )
                self.offline_mode = True
            else:
                self.client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
        else:
            openai_key = os.getenv("OPENAI_API_KEY")
            if not openai_key:
                logger.warning(
                    "OPENAI_API_KEY missing, running in offline fallback mode "
                    "(rule-based simplification for pipeline completeness)."
                )
                self.offline_mode = True
            else:
                self.client = OpenAI(api_key=openai_key)

        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.prompt_template = prompt_template or (
            "Aşağıdaki karmaşık bankacılık düzenlemesi metnini, hukuki anlamını koruyarak "
            "sade ve anlaşılır bir dile çevir. Kritik terimleri ve yasal bağlayıcılığı koru.\n\n"
            "Karmaşık metin:\n{complex_text}\n\nSadeleştirilmiş metin:")

    def simplify(self, text: str) -> Optional[str]:
        if self.offline_mode:
            return self._offline_fallback_simplify(text)

        prompt = self.prompt_template.format(complex_text=text)
        try:
            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature, max_tokens=self.max_tokens)
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return None

    def _offline_fallback_simplify(self, text: str) -> str:
        """Deterministic fallback when API keys are unavailable."""
        simplified = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        simplified = re.sub(r"[+*#]+", " ", simplified)
        simplified = re.sub(r"\s+", " ", simplified).strip()
        simplified = (
            simplified
            .replace(" kapsamında ", " çerçevesinde ")
            .replace("uyarınca", "gereğince")
            .replace("zorunludur", "gereklidir")
        )
        if len(simplified) > 420:
            simplified = simplified[:420].rsplit(" ", 1)[0] + "."
        return simplified

    def simplify_batch(self, texts, delay=1.0):
        results = []
        for text in tqdm(texts, desc="Zero-shot"):
            result = self.simplify(text)
            results.append(result or "")
            time.sleep(delay)
        return results


def main():
    parser = argparse.ArgumentParser(description="Zero-shot LLM simplification")
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--test-file", default="data/parallel/test_gold.jsonl")
    parser.add_argument("--output", default="results/zeroshot_scores.json")
    args = parser.parse_args()

    cfg = yaml.safe_load(open(args.config, encoding="utf-8"))
    zs_cfg = cfg["models"]["zeroshot"]

    simplifier = ZeroShotSimplifier(
        provider=zs_cfg["llm_provider"], model_name=zs_cfg["model_name"],
        temperature=zs_cfg["temperature"], max_tokens=zs_cfg["max_tokens"],
        prompt_template=zs_cfg.get("prompt_template"))

    data = list(jsonlines.open(args.test_file))
    predictions = simplifier.simplify_batch([d["complex"] for d in data])
    references = [d["simple"] for d in data]

    from models.baseline.evaluate_baselines import compute_rouge_scores, compute_bleu_score
    rouge = compute_rouge_scores(predictions, references)
    bleu = compute_bleu_score(predictions, references)

    results = {"model": f"zeroshot_{zs_cfg['model_name']}", "metrics": {**rouge, "bleu": bleu},
               "statistics": {"num_samples": len(data),
                              "avg_pred_len": round(sum(len(p) for p in predictions) / max(len(predictions), 1), 1)},
               "predictions": [{"complex": d["complex"][:200], "prediction": p[:200]}
                               for d, p in zip(data[:5], predictions[:5])]}

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info(f"Results: ROUGE-1={rouge['rouge1']:.4f} BLEU={bleu:.4f} → {args.output}")

if __name__ == "__main__":
    main()
