"""
Gold Standard Manager

Provides tools for manually reviewing and annotating the synthetic
parallel dataset to create a gold standard test set.
Supports interactive review and quality scoring.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import jsonlines

sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def interactive_review(
    input_file: str = "data/parallel/test_gold.jsonl",
    output_file: str = "data/parallel/test_gold_reviewed.jsonl",
    start_index: int = 0,
):
    """
    Interactively review and annotate test set items.
    
    For each item, the reviewer can:
    - Accept the simplification as-is
    - Edit the simplified version
    - Reject the pair (mark as low quality)
    - Score the quality (1-5)
    
    Args:
        input_file: Input JSONL file with parallel pairs
        output_file: Output JSONL file with annotations
        start_index: Index to resume from
    """
    # Load data
    data = []
    with jsonlines.open(input_file) as reader:
        for item in reader:
            data.append(item)
    
    # Load existing reviewed data if resuming
    reviewed = []
    if os.path.exists(output_file):
        with jsonlines.open(output_file) as reader:
            for item in reader:
                reviewed.append(item)
        logger.info(f"Resuming from {len(reviewed)} previously reviewed items")
    
    reviewed_ids = {r["id"] for r in reviewed}
    
    print("\n" + "=" * 70)
    print("GOLD STANDARD REVIEW TOOL")
    print("=" * 70)
    print(f"Total items: {len(data)}")
    print(f"Already reviewed: {len(reviewed)}")
    print(f"Remaining: {len(data) - len(reviewed)}")
    print("=" * 70)
    print()
    print("Commands:")
    print("  [Enter]  Accept as-is")
    print("  [e]      Edit simplified text")
    print("  [r]      Reject this pair")
    print("  [s]      Skip")
    print("  [q]      Quit and save")
    print()
    
    for idx, item in enumerate(data[start_index:], start=start_index):
        if item["id"] in reviewed_ids:
            continue
        
        print(f"\n--- Item {idx + 1}/{len(data)} [{item['id']}] ---")
        print(f"\n📜 KARMAŞIK METİN:")
        print(f"   {item['complex'][:500]}")
        if len(item['complex']) > 500:
            print(f"   ... ({len(item['complex'])} total chars)")
        
        print(f"\n✨ SADELEŞTİRİLMİŞ METİN:")
        print(f"   {item['simple'][:500]}")
        if len(item['simple']) > 500:
            print(f"   ... ({len(item['simple'])} total chars)")
        
        # Get quality score
        while True:
            score_input = input("\n📊 Kalite puanı (1-5, 1=kötü, 5=mükemmel): ").strip()
            if score_input in ["q", "Q"]:
                _save_reviewed(reviewed, output_file)
                return
            try:
                quality_score = int(score_input)
                if 1 <= quality_score <= 5:
                    break
            except ValueError:
                pass
            print("  Lütfen 1-5 arası bir sayı girin")
        
        # Get action
        action = input("İşlem [Enter=kabul, e=düzenle, r=reddet, s=atla, q=çık]: ").strip().lower()
        
        if action == "q":
            _save_reviewed(reviewed, output_file)
            return
        elif action == "s":
            continue
        elif action == "r":
            item_reviewed = {
                **item,
                "review": {
                    "status": "rejected",
                    "quality_score": quality_score,
                    "is_gold": False,
                }
            }
        elif action == "e":
            print("\nYeni sadeleştirilmiş metni girin (bitirmek için boş satır):")
            lines = []
            while True:
                line = input()
                if not line:
                    break
                lines.append(line)
            
            edited_text = "\n".join(lines)
            if edited_text.strip():
                item_reviewed = {
                    **item,
                    "simple": edited_text.strip(),
                    "review": {
                        "status": "edited",
                        "quality_score": quality_score,
                        "is_gold": True,
                        "original_simple": item["simple"],
                    }
                }
            else:
                item_reviewed = {
                    **item,
                    "review": {
                        "status": "accepted",
                        "quality_score": quality_score,
                        "is_gold": True,
                    }
                }
        else:
            # Accept as-is
            item_reviewed = {
                **item,
                "review": {
                    "status": "accepted",
                    "quality_score": quality_score,
                    "is_gold": True,
                }
            }
        
        reviewed.append(item_reviewed)
        reviewed_ids.add(item["id"])
        
        # Auto-save every 10 items
        if len(reviewed) % 10 == 0:
            _save_reviewed(reviewed, output_file)
            logger.info(f"Auto-saved {len(reviewed)} reviewed items")
    
    _save_reviewed(reviewed, output_file)
    _print_review_stats(reviewed)


def _save_reviewed(reviewed: list, output_file: str):
    """Save reviewed items to file."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with jsonlines.open(output_file, mode="w") as writer:
        for item in reviewed:
            writer.write(item)
    logger.info(f"Saved {len(reviewed)} reviewed items to {output_file}")


def _print_review_stats(reviewed: list):
    """Print review statistics."""
    total = len(reviewed)
    if total == 0:
        return
    
    accepted = sum(1 for r in reviewed if r.get("review", {}).get("status") == "accepted")
    edited = sum(1 for r in reviewed if r.get("review", {}).get("status") == "edited")
    rejected = sum(1 for r in reviewed if r.get("review", {}).get("status") == "rejected")
    gold = sum(1 for r in reviewed if r.get("review", {}).get("is_gold", False))
    
    scores = [r["review"]["quality_score"] for r in reviewed if "review" in r]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    print(f"\n📊 Review Statistics:")
    print(f"   Total reviewed: {total}")
    print(f"   Accepted: {accepted}")
    print(f"   Edited: {edited}")
    print(f"   Rejected: {rejected}")
    print(f"   Gold standard: {gold}")
    print(f"   Avg quality score: {avg_score:.2f}")


def export_gold_standard(
    reviewed_file: str = "data/parallel/test_gold_reviewed.jsonl",
    output_file: str = "data/parallel/test_gold_final.jsonl",
    min_quality: int = 3,
):
    """
    Export only gold standard items (accepted/edited with sufficient quality).
    
    Args:
        reviewed_file: Reviewed data file
        output_file: Output file for gold standard only
        min_quality: Minimum quality score to include
    """
    gold_items = []
    
    with jsonlines.open(reviewed_file) as reader:
        for item in reader:
            review = item.get("review", {})
            if review.get("is_gold", False) and review.get("quality_score", 0) >= min_quality:
                # Clean up for export
                export_item = {
                    "id": item["id"],
                    "complex": item["complex"],
                    "simple": item["simple"],
                    "source": "gold_standard",
                    "quality_score": review["quality_score"],
                    "metadata": item.get("metadata", {}),
                }
                gold_items.append(export_item)
    
    with jsonlines.open(output_file, mode="w") as writer:
        for item in gold_items:
            writer.write(item)
    
    logger.info(f"Exported {len(gold_items)} gold standard items to {output_file}")
    return len(gold_items)


def main():
    """CLI entry point for gold standard management."""
    parser = argparse.ArgumentParser(
        description="Gold standard review and management tool"
    )
    parser.add_argument(
        "action", choices=["review", "export", "stats"],
        help="Action to perform"
    )
    parser.add_argument("--input", default="data/parallel/test_gold.jsonl")
    parser.add_argument("--output", default=None)
    parser.add_argument("--min-quality", type=int, default=3)
    
    args = parser.parse_args()
    
    if args.action == "review":
        interactive_review(
            input_file=args.input,
            output_file=args.output or "data/parallel/test_gold_reviewed.jsonl",
        )
    elif args.action == "export":
        export_gold_standard(
            reviewed_file=args.output or "data/parallel/test_gold_reviewed.jsonl",
            output_file="data/parallel/test_gold_final.jsonl",
            min_quality=args.min_quality,
        )
    elif args.action == "stats":
        reviewed = []
        review_file = args.output or "data/parallel/test_gold_reviewed.jsonl"
        if os.path.exists(review_file):
            with jsonlines.open(review_file) as reader:
                reviewed = list(reader)
        _print_review_stats(reviewed)


if __name__ == "__main__":
    main()
