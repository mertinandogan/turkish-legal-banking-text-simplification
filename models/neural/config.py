"""
Neural Model Configuration

Centralized configuration for mT5/BART model training with LoRA.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LoRAConfig:
    """LoRA (Low-Rank Adaptation) hyperparameters."""
    r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.1
    target_modules: list[str] = field(default_factory=lambda: ["q", "v"])
    task_type: str = "SEQ_2_SEQ_LM"


@dataclass
class TrainingConfig:
    """Training hyperparameters."""
    epochs: int = 5
    batch_size: int = 8
    learning_rate: float = 3e-4
    weight_decay: float = 0.01
    warmup_steps: int = 100
    eval_steps: int = 200
    save_steps: int = 500
    gradient_accumulation_steps: int = 4
    fp16: bool = False
    output_dir: str = "results/neural_checkpoints"
    logging_dir: str = "results/logs"
    seed: int = 42
    max_grad_norm: float = 1.0


@dataclass
class InferenceConfig:
    """Inference/generation hyperparameters."""
    beam_size: int = 4
    length_penalty: float = 1.0
    no_repeat_ngram_size: int = 3
    early_stopping: bool = True
    max_length: int = 256
    min_length: int = 20


@dataclass
class ModelConfig:
    """Complete model configuration."""
    model_name: str = "google/mt5-small"
    tokenizer_name: str = "google/mt5-small"
    max_source_length: int = 512
    max_target_length: int = 256
    
    lora: LoRAConfig = field(default_factory=LoRAConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    inference: InferenceConfig = field(default_factory=InferenceConfig)
    
    @classmethod
    def from_yaml(cls, config: dict) -> "ModelConfig":
        """Create ModelConfig from YAML config dictionary."""
        neural = config.get("models", {}).get("neural", {})
        
        lora_dict = neural.get("lora", {})
        training_dict = neural.get("training", {})
        inference_dict = neural.get("inference", {})
        
        return cls(
            model_name=neural.get("model_name", cls.model_name),
            tokenizer_name=neural.get("tokenizer_name", cls.tokenizer_name),
            max_source_length=neural.get("max_source_length", cls.max_source_length),
            max_target_length=neural.get("max_target_length", cls.max_target_length),
            lora=LoRAConfig(**{k: v for k, v in lora_dict.items() if k in LoRAConfig.__dataclass_fields__}),
            training=TrainingConfig(**{k: v for k, v in training_dict.items() if k in TrainingConfig.__dataclass_fields__}),
            inference=InferenceConfig(**{k: v for k, v in inference_dict.items() if k in InferenceConfig.__dataclass_fields__}),
        )
