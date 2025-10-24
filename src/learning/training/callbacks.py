"""
Callback Factory

학습 콜백 생성 및 관리
"""
from typing import List
from pathlib import Path
import tensorflow as tf

from src.learning.training.config import TrainingConfig


class CallbackFactory:
    """콜백 생성 팩토리"""

    @staticmethod
    def create_callbacks(config: TrainingConfig) -> List[tf.keras.callbacks.Callback]:
        """
        Create callbacks from config

        Args:
            config: TrainingConfig

        Returns:
            List of Keras callbacks
        """
        callbacks = []

        # EarlyStopping
        if config.use_early_stopping:
            callbacks.append(
                tf.keras.callbacks.EarlyStopping(
                    monitor=config.early_stopping_monitor,
                    patience=config.early_stopping_patience,
                    restore_best_weights=True,
                    verbose=1
                )
            )

        # ReduceLROnPlateau
        if config.use_reduce_lr:
            callbacks.append(
                tf.keras.callbacks.ReduceLROnPlateau(
                    monitor=config.reduce_lr_monitor,
                    factor=config.reduce_lr_factor,
                    patience=config.reduce_lr_patience,
                    verbose=1,
                    min_lr=1e-7
                )
            )

        # ModelCheckpoint
        if config.use_model_checkpoint:
            checkpoint_dir = Path(config.output_dir) / "checkpoints"
            checkpoint_dir.mkdir(parents=True, exist_ok=True)

            checkpoint_path = checkpoint_dir / f"{config.model_name}_best.h5"

            callbacks.append(
                tf.keras.callbacks.ModelCheckpoint(
                    filepath=str(checkpoint_path),
                    monitor=config.checkpoint_monitor,
                    mode=config.checkpoint_mode,
                    save_best_only=config.save_best_only,
                    verbose=1
                )
            )

        return callbacks
