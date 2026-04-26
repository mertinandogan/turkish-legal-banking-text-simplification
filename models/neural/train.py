"""
Neural Model Training

Fine-tunes mT5-small (or mBART) with LoRA for text simplification.
Uses Hugging Face Transformers + PEFT for parameter-efficient fine-tuning.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

import torch
import yaml
from tqdm import tqdm
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    get_linear_schedule_with_warmup,
)
from peft import LoraConfig, get_peft_model, TaskType

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.neural.config import ModelConfig
from models.neural.dataset import create_dataloaders

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def setup_model_and_tokenizer(config: ModelConfig):
    """
    Load pretrained model and tokenizer, apply LoRA.
    
    Args:
        config: Model configuration
        
    Returns:
        Tuple of (model, tokenizer)
    """
    logger.info(f"Loading model: {config.model_name}")
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(config.tokenizer_name)
    
    # Load model
    model = AutoModelForSeq2SeqLM.from_pretrained(config.model_name)
    
    # Apply LoRA
    task_type_map = {
        "SEQ_2_SEQ_LM": TaskType.SEQ_2_SEQ_LM,
        "CAUSAL_LM": TaskType.CAUSAL_LM,
    }
    
    lora_config = LoraConfig(
        task_type=task_type_map.get(config.lora.task_type, TaskType.SEQ_2_SEQ_LM),
        r=config.lora.r,
        lora_alpha=config.lora.lora_alpha,
        lora_dropout=config.lora.lora_dropout,
        target_modules=config.lora.target_modules,
    )
    
    model = get_peft_model(model, lora_config)
    
    # Log trainable parameters
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    logger.info(
        f"LoRA applied: {trainable_params:,} trainable params "
        f"/ {total_params:,} total ({trainable_params/total_params*100:.2f}%)"
    )
    
    return model, tokenizer


def train_epoch(
    model,
    train_loader,
    optimizer,
    scheduler,
    device,
    gradient_accumulation_steps: int = 4,
    max_grad_norm: float = 1.0,
    epoch: int = 0,
) -> float:
    """
    Train for one epoch.
    
    Returns:
        Average training loss
    """
    model.train()
    total_loss = 0
    num_steps = 0
    
    progress = tqdm(train_loader, desc=f"Epoch {epoch + 1} [Train]")
    
    for step, batch in enumerate(progress):
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)
        
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels,
        )
        
        loss = outputs.loss / gradient_accumulation_steps
        loss.backward()
        
        if (step + 1) % gradient_accumulation_steps == 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
            num_steps += 1
        
        total_loss += outputs.loss.item()
        progress.set_postfix({"loss": f"{outputs.loss.item():.4f}"})
    
    avg_loss = total_loss / len(train_loader) if train_loader else 0
    return avg_loss


def evaluate(model, val_loader, device, epoch: int = 0) -> float:
    """
    Evaluate on validation set.
    
    Returns:
        Average validation loss
    """
    model.eval()
    total_loss = 0
    
    with torch.no_grad():
        for batch in tqdm(val_loader, desc=f"Epoch {epoch + 1} [Eval]"):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)
            
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels,
            )
            
            total_loss += outputs.loss.item()
    
    avg_loss = total_loss / len(val_loader) if val_loader else 0
    return avg_loss


def train(
    config: ModelConfig,
    train_file: str = "data/parallel/train.jsonl",
    val_file: str = "data/parallel/val.jsonl",
):
    """
    Full training loop.
    
    Args:
        config: Model configuration
        train_file: Training data path
        val_file: Validation data path
    """
    # Device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")
    
    if device.type == "cuda":
        logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
        logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f} GB")
    
    # Setup model
    model, tokenizer = setup_model_and_tokenizer(config)
    model = model.to(device)
    
    # Create dataloaders
    train_loader, val_loader = create_dataloaders(
        train_file=train_file,
        val_file=val_file,
        tokenizer=tokenizer,
        batch_size=config.training.batch_size,
        max_source_length=config.max_source_length,
        max_target_length=config.max_target_length,
    )
    
    logger.info(f"Train batches: {len(train_loader)}, Val batches: {len(val_loader)}")
    
    # Optimizer
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config.training.learning_rate,
        weight_decay=config.training.weight_decay,
    )
    
    # Scheduler
    total_steps = (
        len(train_loader) // config.training.gradient_accumulation_steps
        * config.training.epochs
    )
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=config.training.warmup_steps,
        num_training_steps=total_steps,
    )
    
    # Training loop
    os.makedirs(config.training.output_dir, exist_ok=True)
    best_val_loss = float("inf")
    training_log = []
    
    for epoch in range(config.training.epochs):
        logger.info(f"\n{'='*50}")
        logger.info(f"Epoch {epoch + 1}/{config.training.epochs}")
        logger.info(f"{'='*50}")
        
        # Train
        train_loss = train_epoch(
            model=model,
            train_loader=train_loader,
            optimizer=optimizer,
            scheduler=scheduler,
            device=device,
            gradient_accumulation_steps=config.training.gradient_accumulation_steps,
            max_grad_norm=config.training.max_grad_norm,
            epoch=epoch,
        )
        
        # Evaluate
        val_loss = evaluate(model, val_loader, device, epoch)
        
        logger.info(
            f"Epoch {epoch + 1}: "
            f"Train Loss = {train_loss:.4f}, "
            f"Val Loss = {val_loss:.4f}"
        )
        
        training_log.append({
            "epoch": epoch + 1,
            "train_loss": train_loss,
            "val_loss": val_loss,
            "learning_rate": scheduler.get_last_lr()[0],
        })
        
        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_path = os.path.join(config.training.output_dir, "best_model")
            model.save_pretrained(best_path)
            tokenizer.save_pretrained(best_path)
            logger.info(f"✅ Best model saved (val_loss={val_loss:.4f})")
        
        # Save checkpoint
        if (epoch + 1) % 2 == 0 or epoch == config.training.epochs - 1:
            ckpt_path = os.path.join(
                config.training.output_dir, f"checkpoint-epoch-{epoch+1}"
            )
            model.save_pretrained(ckpt_path)
            tokenizer.save_pretrained(ckpt_path)
    
    # Save training log
    import json
    log_path = os.path.join(config.training.output_dir, "training_log.json")
    with open(log_path, "w") as f:
        json.dump(training_log, f, indent=2)
    
    logger.info(f"\n🎉 Training complete! Best val loss: {best_val_loss:.4f}")
    logger.info(f"Best model: {os.path.join(config.training.output_dir, 'best_model')}")
    
    return training_log


def main():
    """CLI entry point for training."""
    parser = argparse.ArgumentParser(description="Train neural text simplification model")
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--train-file", default="data/parallel/train.jsonl")
    parser.add_argument("--val-file", default="data/parallel/val.jsonl")
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--lr", type=float, default=None)
    
    args = parser.parse_args()
    
    # Load config
    yaml_config = yaml.safe_load(open(args.config, encoding="utf-8"))
    config = ModelConfig.from_yaml(yaml_config)
    
    # Override from CLI
    if args.epochs:
        config.training.epochs = args.epochs
    if args.batch_size:
        config.training.batch_size = args.batch_size
    if args.lr:
        config.training.learning_rate = args.lr
    
    train(
        config=config,
        train_file=args.train_file,
        val_file=args.val_file,
    )


if __name__ == "__main__":
    main()
