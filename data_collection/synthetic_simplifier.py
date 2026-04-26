"""
Synthetic Simplifier

Uses an LLM API (OpenRouter / OpenAI) to generate simplified versions
of complex banking regulation paragraphs, creating a parallel dataset
for training the neural text simplification model.
"""

import argparse
import asyncio
import json
import logging
import os
import random
import sys
from pathlib import Path
from typing import Optional

import yaml
import jsonlines
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Simplification prompt template
SIMPLIFICATION_PROMPT = """Sen bir bankacılık hukuku uzmanısın. Görevin, karmaşık bankacılık düzenlemesi metinlerini 
sade ve anlaşılır bir dile çevirmek. Aşağıdaki kurallara uy:

1. Hukuki anlamı ve bağlayıcılığı koru
2. Teknik terimleri mümkün olduğunca açıkla veya sadeleştir
3. Uzun cümleleri kısa cümlelere böl
4. Pasif yapıları aktif yapılara çevir (mümkünse)
5. Gereksiz jargonu kaldır ama kritik hukuki kavramları koru
6. Anlamı değiştirme, sadece ifade biçimini sadeleştir

Karmaşık metin:
{complex_text}

Sadeleştirilmiş metin:"""


class SyntheticSimplifier:
    """Generates simplified versions of complex texts using LLM."""
    
    def __init__(
        self,
        provider: str = "openrouter",
        model_name: str = "google/gemini-2.0-flash-001",
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ):
        """
        Initialize the simplifier.
        
        Args:
            provider: LLM provider ("openrouter" or "openai")
            model_name: Model identifier
            temperature: Generation temperature
            max_tokens: Maximum output tokens
        """
        self.provider = provider
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize client
        from openai import OpenAI
        
        if provider == "openrouter":
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENROUTER_API_KEY environment variable is required. "
                    "Get one at https://openrouter.ai/"
                )
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
            )
        elif provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")
            self.client = OpenAI(api_key=api_key)
        else:
            raise ValueError(f"Unknown provider: {provider}")
        
        logger.info(f"SyntheticSimplifier initialized: {provider}/{model_name}")
    
    def simplify(self, complex_text: str) -> Optional[str]:
        """
        Generate a simplified version of the complex text.
        
        Args:
            complex_text: Complex banking regulation text
            
        Returns:
            Simplified text or None if failed
        """
        prompt = SIMPLIFICATION_PROMPT.format(complex_text=complex_text)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "Sen Türk bankacılık düzenlemelerini sadeleştiren bir uzmansın."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            
            simplified = response.choices[0].message.content.strip()
            
            # Basic quality check
            if len(simplified) < 20:
                logger.warning(f"Generated text too short: {len(simplified)} chars")
                return None
            
            return simplified
            
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return None
    
    def simplify_batch(
        self,
        paragraphs: list[dict],
        batch_size: int = 10,
        delay: float = 2.0,
    ) -> list[dict]:
        """
        Simplify a batch of paragraphs.
        
        Args:
            paragraphs: List of paragraph dicts with 'complex_text'
            batch_size: Number of items per batch
            delay: Delay between batches in seconds
            
        Returns:
            List of parallel pairs (complex + simplified)
        """
        results = []
        total = len(paragraphs)
        
        for i in tqdm(range(0, total, batch_size), desc="Simplifying"):
            batch = paragraphs[i:i + batch_size]
            
            for para in batch:
                simplified = self.simplify(para["complex_text"])
                
                if simplified:
                    result = {
                        "id": para["id"],
                        "complex": para["complex_text"],
                        "simple": simplified,
                        "source": f"synthetic_{self.model_name.split('/')[-1]}",
                        "metadata": para.get("metadata", {}),
                    }
                    results.append(result)
                    logger.debug(
                        f"✅ {para['id']}: "
                        f"{len(para['complex_text'])} → {len(simplified)} chars"
                    )
                else:
                    logger.warning(f"⚠️ Failed to simplify {para['id']}")
            
            # Rate limiting between batches
            if i + batch_size < total:
                import time
                time.sleep(delay)
        
        logger.info(
            f"Simplified {len(results)}/{total} paragraphs "
            f"({len(results)/total*100:.1f}% success rate)"
        )
        
        return results


def split_dataset(
    data: list[dict],
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42,
) -> tuple[list, list, list]:
    """
    Split data into train/val/test sets.
    
    Args:
        data: Full dataset
        train_ratio: Training set ratio
        val_ratio: Validation set ratio
        test_ratio: Test set ratio
        seed: Random seed
        
    Returns:
        Tuple of (train, val, test) lists
    """
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6
    
    random.seed(seed)
    shuffled = data.copy()
    random.shuffle(shuffled)
    
    n = len(shuffled)
    train_end = int(n * train_ratio)
    val_end = train_end + int(n * val_ratio)
    
    train = shuffled[:train_end]
    val = shuffled[train_end:val_end]
    test = shuffled[val_end:]
    
    return train, val, test


def create_parallel_dataset(
    input_file: str = "data/paragraphs/complex_paragraphs.jsonl",
    train_output: str = "data/parallel/train.jsonl",
    val_output: str = "data/parallel/val.jsonl",
    test_output: str = "data/parallel/test_gold.jsonl",
    provider: str = "openrouter",
    model_name: str = "google/gemini-2.0-flash-001",
    temperature: float = 0.3,
    max_tokens: int = 1024,
    batch_size: int = 10,
    delay: float = 2.0,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    max_paragraphs: Optional[int] = None,
) -> dict:
    """
    Create the full parallel dataset from extracted paragraphs.
    
    Args:
        input_file: Path to extracted paragraphs JSONL
        train_output: Training set output path
        val_output: Validation set output path
        test_output: Test set output path
        provider: LLM provider
        model_name: LLM model name
        temperature: Generation temperature
        max_tokens: Max output tokens
        batch_size: Processing batch size
        delay: Delay between batches
        train_ratio: Training set ratio
        val_ratio: Validation set ratio
        test_ratio: Test set ratio
        max_paragraphs: Limit number of paragraphs to process
        
    Returns:
        Dataset statistics
    """
    # Load paragraphs
    paragraphs = []
    with jsonlines.open(input_file) as reader:
        for item in reader:
            paragraphs.append(item)
    
    logger.info(f"Loaded {len(paragraphs)} paragraphs from {input_file}")
    
    if max_paragraphs:
        paragraphs = paragraphs[:max_paragraphs]
        logger.info(f"Limited to {max_paragraphs} paragraphs")
    
    # Initialize simplifier
    simplifier = SyntheticSimplifier(
        provider=provider,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    
    # Generate simplified versions
    parallel_data = simplifier.simplify_batch(
        paragraphs=paragraphs,
        batch_size=batch_size,
        delay=delay,
    )
    
    if not parallel_data:
        logger.error("No parallel data generated!")
        return {"error": "No data generated"}
    
    # Split into train/val/test
    train, val, test = split_dataset(
        parallel_data,
        train_ratio=train_ratio,
        val_ratio=val_ratio,
        test_ratio=test_ratio,
    )
    
    # Save datasets
    for data, path in [(train, train_output), (val, val_output), (test, test_output)]:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with jsonlines.open(path, mode="w") as writer:
            for item in data:
                writer.write(item)
    
    stats = {
        "total_generated": len(parallel_data),
        "train_size": len(train),
        "val_size": len(val),
        "test_size": len(test),
        "avg_complex_length": round(
            sum(len(d["complex"]) for d in parallel_data) / len(parallel_data), 1
        ),
        "avg_simple_length": round(
            sum(len(d["simple"]) for d in parallel_data) / len(parallel_data), 1
        ),
        "compression_ratio": round(
            sum(len(d["simple"]) for d in parallel_data)
            / sum(len(d["complex"]) for d in parallel_data),
            3,
        ),
    }
    
    # Save stats
    stats_file = os.path.join(os.path.dirname(train_output), "dataset_stats.json")
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    logger.info(
        f"\n📊 Dataset created:\n"
        f"   Total pairs: {stats['total_generated']}\n"
        f"   Train: {stats['train_size']}\n"
        f"   Validation: {stats['val_size']}\n"
        f"   Test: {stats['test_size']}\n"
        f"   Avg complex length: {stats['avg_complex_length']} chars\n"
        f"   Avg simple length: {stats['avg_simple_length']} chars\n"
        f"   Compression ratio: {stats['compression_ratio']}"
    )
    
    return stats


def main():
    """CLI entry point for synthetic dataset creation."""
    parser = argparse.ArgumentParser(
        description="Create synthetic parallel dataset for text simplification"
    )
    parser.add_argument(
        "--config", default="configs/default.yaml",
        help="Configuration file path"
    )
    parser.add_argument(
        "--max-paragraphs", type=int, default=None,
        help="Limit number of paragraphs to process (for testing)"
    )
    parser.add_argument(
        "--input-file", default=None,
        help="Override input paragraphs file"
    )
    
    args = parser.parse_args()
    
    config = yaml.safe_load(open(args.config, encoding="utf-8"))
    synth_config = config["data_collection"]["synthetic_simplification"]
    
    create_parallel_dataset(
        input_file=args.input_file or config["data_collection"]["paragraph_extraction"]["output_file"],
        train_output=synth_config["train_output"],
        val_output=synth_config["val_output"],
        test_output=synth_config["test_output"],
        provider=synth_config["llm_provider"],
        model_name=synth_config["model_name"],
        temperature=synth_config["temperature"],
        max_tokens=synth_config["max_tokens"],
        batch_size=synth_config["batch_size"],
        delay=synth_config["delay_between_batches"],
        train_ratio=synth_config["train_ratio"],
        val_ratio=synth_config["val_ratio"],
        test_ratio=synth_config["test_ratio"],
        max_paragraphs=args.max_paragraphs,
    )


if __name__ == "__main__":
    main()
