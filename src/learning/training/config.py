"""
Training Configuration

학습 설정 관리
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
import yaml


@dataclass
class TrainingConfig:
    """학습 설정"""

    # Model
    architecture: str = "dense"
    model_name: str = "block_classifier_v1"
    model_version: str = "1.0"

    # Data
    batch_size: int = 32
    validation_split: float = 0.2
    shuffle: bool = True
    random_seed: int = 42

    # Training
    epochs: int = 100
    learning_rate: float = 0.001
    optimizer: str = "adam"

    # Callbacks
    use_early_stopping: bool = True
    early_stopping_patience: int = 10
    early_stopping_monitor: str = "val_loss"

    use_reduce_lr: bool = True
    reduce_lr_patience: int = 5
    reduce_lr_factor: float = 0.5
    reduce_lr_monitor: str = "val_loss"

    use_model_checkpoint: bool = True
    checkpoint_monitor: str = "val_accuracy"
    checkpoint_mode: str = "max"
    save_best_only: bool = True

    # Hyperparameters (model-specific)
    hyperparameters: Dict[str, Any] = field(default_factory=dict)

    # Output
    output_dir: str = "models"
    save_history: bool = True

    # Metadata
    description: str = ""
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrainingConfig':
        """Create from dictionary"""
        return cls(**data)

    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'TrainingConfig':
        """Load from YAML file"""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)

    def to_yaml(self, yaml_path: str):
        """Save to YAML file"""
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, allow_unicode=True)
