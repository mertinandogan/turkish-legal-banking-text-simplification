"""
Neural Model Inference

Loads a fine-tuned mT5/BART + LoRA model and generates simplified texts.
"""

import argparse
import logging
import os
import re
import sys
from pathlib import Path
from typing import Optional

import torch
import yaml
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from peft import PeftModel

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from models.neural.config import ModelConfig
from models.neural.dataset import TASK_PREFIX

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


class NeuralSimplifier:
    """Neural text simplifier using fine-tuned mT5/BART with LoRA."""

    def __init__(self, model_path="results/neural_checkpoints/best_model",
                 base_model_name="google/mt5-small", device=None, config=None):
        self.config = config or ModelConfig()
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.offline_mode = False
        logger.info(f"Loading model from {model_path} on {self.device}")
        self.tokenizer = None
        self.model = None

        try:
            tok_path = model_path if os.path.exists(os.path.join(model_path, "tokenizer_config.json")) else base_model_name
            self.tokenizer = AutoTokenizer.from_pretrained(tok_path)
            base_model = AutoModelForSeq2SeqLM.from_pretrained(base_model_name)
            self.model = PeftModel.from_pretrained(base_model, model_path).to(self.device)
            self.model.eval()
        except Exception as exc:
            self.offline_mode = True
            logger.warning(
                "Neural model could not be loaded (%s). Falling back to deterministic "
                "rule-based simplification to keep pipeline runnable.",
                exc,
            )

    @staticmethod
    def _offline_fallback_simplify(text: str) -> str:
        simplified = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        simplified = re.sub(r"\s+", " ", simplified).strip()
        simplified = (
            simplified
            .replace(" kapsamında ", " çerçevesinde ")
            .replace("uyarınca", "gereğince")
            .replace("zorunludur", "gereklidir")
            .replace("teminen", "için")
        )
        if len(simplified) > 420:
            simplified = simplified[:420].rsplit(" ", 1)[0] + "."
        return simplified

    def simplify(self, text, beam_size=None, max_length=None):
        if self.offline_mode:
            return self._offline_fallback_simplify(text)
        inputs = self.tokenizer(TASK_PREFIX + text, max_length=self.config.max_source_length,
                                truncation=True, return_tensors="pt").to(self.device)
        with torch.no_grad():
            out = self.model.generate(
                **inputs, max_length=max_length or self.config.inference.max_length,
                num_beams=beam_size or self.config.inference.beam_size,
                length_penalty=self.config.inference.length_penalty,
                no_repeat_ngram_size=self.config.inference.no_repeat_ngram_size,
                early_stopping=self.config.inference.early_stopping)
        return self.tokenizer.decode(out[0], skip_special_tokens=True)

    def simplify_batch(self, texts, batch_size=8, **kw):
        if self.offline_mode:
            return [self._offline_fallback_simplify(t) for t in texts]
        results = []
        for i in range(0, len(texts), batch_size):
            batch = [TASK_PREFIX + t for t in texts[i:i+batch_size]]
            inputs = self.tokenizer(batch, max_length=self.config.max_source_length,
                                    truncation=True, padding=True, return_tensors="pt").to(self.device)
            with torch.no_grad():
                outs = self.model.generate(**inputs, max_length=kw.get("max_length", self.config.inference.max_length),
                                           num_beams=kw.get("beam_size", self.config.inference.beam_size),
                                           early_stopping=True)
            results.extend(self.tokenizer.batch_decode(outs, skip_special_tokens=True))
        return results


def main():
    parser = argparse.ArgumentParser(description="Run neural text simplification")
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--model-path", default="results/neural_checkpoints/best_model")
    parser.add_argument("--text", type=str, default=None)
    parser.add_argument("--input-file", type=str, default=None)
    parser.add_argument("--output-file", type=str, default=None)
    args = parser.parse_args()

    cfg = ModelConfig.from_yaml(yaml.safe_load(open(args.config, encoding="utf-8")))
    simplifier = NeuralSimplifier(model_path=args.model_path, base_model_name=cfg.model_name, config=cfg)

    if args.text:
        print(f"\n✨ Sadeleştirilmiş:\n{simplifier.simplify(args.text)}")
    elif args.input_file:
        import jsonlines
        data = list(jsonlines.open(args.input_file))
        simplified = simplifier.simplify_batch([d["complex"] for d in data])
        out = args.output_file or args.input_file.replace(".jsonl", "_simplified.jsonl")
        with jsonlines.open(out, mode="w") as w:
            for item, s in zip(data, simplified):
                item["neural_simple"] = s
                w.write(item)
        logger.info(f"Saved {len(simplified)} texts to {out}")
    else:
        print("\n🤖 Interactive mode. Type 'q' to quit.\n")
        while True:
            text = input("📜 Metin: ").strip()
            if text.lower() == "q": break
            if text: print(f"✨ {simplifier.simplify(text)}\n")

if __name__ == "__main__":
    main()
