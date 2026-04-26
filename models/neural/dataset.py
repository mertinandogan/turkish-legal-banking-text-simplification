"""
PyTorch Dataset for Text Simplification

Loads parallel complex-simple pairs and tokenizes them
for sequence-to-sequence model training.
"""

import logging
from typing import Optional

import jsonlines
import torch
from torch.utils.data import Dataset
from transformers import PreTrainedTokenizerBase

logger = logging.getLogger(__name__)

# Task prefix for mT5 (helps the model understand the task)
TASK_PREFIX = "sadeleştir: "


class SimplificationDataset(Dataset):
    """
    PyTorch Dataset for text simplification parallel data.
    
    Loads JSONL files with 'complex' and 'simple' fields,
    tokenizes them using the provided tokenizer.
    """
    
    def __init__(
        self,
        file_path: str,
        tokenizer: PreTrainedTokenizerBase,
        max_source_length: int = 512,
        max_target_length: int = 256,
        add_task_prefix: bool = True,
    ):
        """
        Initialize dataset.
        
        Args:
            file_path: Path to JSONL file with parallel data
            tokenizer: HuggingFace tokenizer
            max_source_length: Maximum source (complex) sequence length
            max_target_length: Maximum target (simple) sequence length
            add_task_prefix: Whether to prepend task prefix to source
        """
        self.tokenizer = tokenizer
        self.max_source_length = max_source_length
        self.max_target_length = max_target_length
        self.add_task_prefix = add_task_prefix
        
        # Load data
        self.data = []
        with jsonlines.open(file_path) as reader:
            for item in reader:
                self.data.append(item)
        
        logger.info(f"Loaded {len(self.data)} examples from {file_path}")
    
    def __len__(self) -> int:
        return len(self.data)
    
    def __getitem__(self, idx: int) -> dict:
        item = self.data[idx]
        
        # Prepare source text
        source = item["complex"]
        if self.add_task_prefix:
            source = TASK_PREFIX + source
        
        target = item["simple"]
        
        # Tokenize source
        source_encoding = self.tokenizer(
            source,
            max_length=self.max_source_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        
        # Tokenize target
        target_encoding = self.tokenizer(
            target,
            max_length=self.max_target_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        
        # Replace padding token id's of labels with -100 so they're ignored in loss
        labels = target_encoding["input_ids"].squeeze()
        labels[labels == self.tokenizer.pad_token_id] = -100
        
        return {
            "input_ids": source_encoding["input_ids"].squeeze(),
            "attention_mask": source_encoding["attention_mask"].squeeze(),
            "labels": labels,
        }


def create_dataloaders(
    train_file: str,
    val_file: str,
    tokenizer: PreTrainedTokenizerBase,
    batch_size: int = 8,
    max_source_length: int = 512,
    max_target_length: int = 256,
    num_workers: int = 0,
) -> tuple:
    """
    Create train and validation DataLoaders.
    
    Args:
        train_file: Training data JSONL path
        val_file: Validation data JSONL path
        tokenizer: HuggingFace tokenizer
        batch_size: Batch size
        max_source_length: Max source sequence length
        max_target_length: Max target sequence length
        num_workers: DataLoader workers
        
    Returns:
        Tuple of (train_loader, val_loader)
    """
    train_dataset = SimplificationDataset(
        file_path=train_file,
        tokenizer=tokenizer,
        max_source_length=max_source_length,
        max_target_length=max_target_length,
    )
    
    val_dataset = SimplificationDataset(
        file_path=val_file,
        tokenizer=tokenizer,
        max_source_length=max_source_length,
        max_target_length=max_target_length,
    )
    
    train_loader = torch.utils.data.DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True,
    )
    
    val_loader = torch.utils.data.DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True,
    )
    
    return train_loader, val_loader
