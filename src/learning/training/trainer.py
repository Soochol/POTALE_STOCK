"""
Model Trainer

모델 학습 오케스트레이터
"""
from typing import Optional, Dict, Any
from pathlib import Path
import json
import numpy as np
import tensorflow as tf

from src.learning.models.model_registry import ModelRegistry, BaseModel, ModelMetadata
from src.learning.training.config import TrainingConfig
from src.learning.training.callbacks import CallbackFactory
from src.learning.evaluation.metrics import EvaluationMetrics, ModelPerformance


class ModelTrainer:
    """모델 학습 관리자"""

    def __init__(self, config: TrainingConfig):
        """
        Args:
            config: TrainingConfig
        """
        self.config = config
        self.model: Optional[BaseModel] = None
        self.history: Optional[tf.keras.callbacks.History] = None

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None
    ) -> tf.keras.callbacks.History:
        """
        Train model

        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features (auto-split if None)
            y_val: Validation labels

        Returns:
            Training history
        """
        # Create model
        if self.model is None:
            input_shape = X_train.shape[1:]
            num_classes = int(np.max(y_train) + 1)
            num_features = X_train.shape[-1] if len(X_train.shape) > 2 else X_train.shape[1]

            self.model = ModelRegistry.create_model(
                architecture=self.config.architecture,
                input_shape=input_shape,
                num_classes=num_classes,
                num_features=num_features,
                **self.config.hyperparameters
            )

        # Build Keras model
        keras_model = self.model.get_model()

        # Create callbacks
        callbacks = CallbackFactory.create_callbacks(self.config)

        # Prepare validation data
        if X_val is None:
            validation_data = None
            validation_split = self.config.validation_split
        else:
            validation_data = (X_val, y_val)
            validation_split = 0.0

        # Train
        self.history = keras_model.fit(
            X_train,
            y_train,
            batch_size=self.config.batch_size,
            epochs=self.config.epochs,
            validation_data=validation_data,
            validation_split=validation_split,
            callbacks=callbacks,
            shuffle=self.config.shuffle,
            verbose=1
        )

        return self.history

    def evaluate(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> ModelPerformance:
        """
        Evaluate model

        Args:
            X_test: Test features
            y_test: Test labels

        Returns:
            ModelPerformance
        """
        if self.model is None:
            raise ValueError("Model not trained yet")

        keras_model = self.model.get_model()

        # Predict
        y_pred_probs = keras_model.predict(X_test, verbose=0)
        y_pred = np.argmax(y_pred_probs, axis=1)

        # Evaluate
        performance = EvaluationMetrics.evaluate_full(
            y_true=y_test,
            y_pred=y_pred,
            model_name=self.config.model_name,
            dataset_name="test_set",
            notes=self.config.description,
            hyperparameters=self.config.hyperparameters
        )

        return performance

    def save_model(self, output_path: Optional[str] = None):
        """
        Save trained model

        Args:
            output_path: Output path (auto-generate if None)
        """
        if self.model is None:
            raise ValueError("Model not trained yet")

        # Determine output path
        if output_path is None:
            output_dir = Path(self.config.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{self.config.model_name}.h5"
        else:
            output_path = Path(output_path)

        # Create metadata
        metadata = self.model.create_metadata(
            model_name=self.config.model_name,
            version=self.config.model_version,
            description=self.config.description,
            tags=self.config.tags
        )

        # Add training info
        if self.history:
            metadata.trained = True
            metadata.training_samples = len(self.history.epoch) * self.config.batch_size

            if 'val_accuracy' in self.history.history:
                metadata.validation_accuracy = float(
                    max(self.history.history['val_accuracy'])
                )

        # Save model
        self.model.save(str(output_path))
        metadata.model_file_path = str(output_path)

        # Save metadata
        metadata_path = output_path.parent / f"{self.config.model_name}_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata.to_dict(), f, indent=2, ensure_ascii=False)

        # Save history
        if self.config.save_history and self.history:
            history_path = output_path.parent / f"{self.config.model_name}_history.json"
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(self.history.history, f, indent=2)

        print(f"✅ Model saved: {output_path}")
        print(f"✅ Metadata saved: {metadata_path}")
