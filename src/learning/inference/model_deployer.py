"""
Model Deployer

모델 로드 및 배포 관리
"""
from typing import Optional, Dict, Any
from pathlib import Path
import json
import tensorflow as tf

from src.learning.models.model_registry import ModelMetadata


class ModelDeployer:
    """모델 배포 관리자"""

    def __init__(self, model_dir: str = "models"):
        """
        Args:
            model_dir: Directory containing saved models
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.loaded_models: Dict[str, tf.keras.Model] = {}
        self.model_metadata: Dict[str, ModelMetadata] = {}

    def load_model(
        self,
        model_name: str,
        model_path: Optional[str] = None
    ) -> tf.keras.Model:
        """
        Load model from file

        Args:
            model_name: Model identifier
            model_path: Path to model file (auto-detect if None)

        Returns:
            Loaded Keras model

        Raises:
            FileNotFoundError: If model file not found
        """
        # Check if already loaded
        if model_name in self.loaded_models:
            return self.loaded_models[model_name]

        # Determine model path
        if model_path is None:
            model_path = self.model_dir / f"{model_name}.h5"
        else:
            model_path = Path(model_path)

        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        # Load model
        model = tf.keras.models.load_model(str(model_path))
        self.loaded_models[model_name] = model

        # Load metadata if exists
        metadata_path = model_path.parent / f"{model_name}_metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata_dict = json.load(f)
                self.model_metadata[model_name] = ModelMetadata.from_dict(metadata_dict)

        return model

    def save_model(
        self,
        model: tf.keras.Model,
        model_name: str,
        metadata: Optional[ModelMetadata] = None,
        model_path: Optional[str] = None
    ):
        """
        Save model to file

        Args:
            model: Keras model to save
            model_name: Model identifier
            metadata: Model metadata
            model_path: Path to save model (auto-generate if None)
        """
        # Determine model path
        if model_path is None:
            model_path = self.model_dir / f"{model_name}.h5"
        else:
            model_path = Path(model_path)

        model_path.parent.mkdir(parents=True, exist_ok=True)

        # Save model
        model.save(str(model_path))

        # Save metadata
        if metadata:
            metadata_path = model_path.parent / f"{model_name}_metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata.to_dict(), f, indent=2, ensure_ascii=False)

            self.model_metadata[model_name] = metadata

        # Cache loaded model
        self.loaded_models[model_name] = model

    def get_model(self, model_name: str) -> Optional[tf.keras.Model]:
        """
        Get loaded model

        Args:
            model_name: Model identifier

        Returns:
            Loaded model or None if not loaded
        """
        return self.loaded_models.get(model_name)

    def get_metadata(self, model_name: str) -> Optional[ModelMetadata]:
        """
        Get model metadata

        Args:
            model_name: Model identifier

        Returns:
            Model metadata or None if not available
        """
        return self.model_metadata.get(model_name)

    def list_loaded_models(self) -> list:
        """
        List all loaded models

        Returns:
            List of model names
        """
        return list(self.loaded_models.keys())

    def list_available_models(self) -> list:
        """
        List all available model files in model directory

        Returns:
            List of model names
        """
        model_files = list(self.model_dir.glob("*.h5"))
        return [f.stem for f in model_files]

    def unload_model(self, model_name: str):
        """
        Unload model from memory

        Args:
            model_name: Model identifier
        """
        if model_name in self.loaded_models:
            del self.loaded_models[model_name]

        if model_name in self.model_metadata:
            del self.model_metadata[model_name]

    def unload_all(self):
        """Unload all models from memory"""
        self.loaded_models.clear()
        self.model_metadata.clear()

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Get comprehensive model information

        Args:
            model_name: Model identifier

        Returns:
            Dictionary with model info

        Raises:
            ValueError: If model not found
        """
        if model_name not in self.loaded_models:
            raise ValueError(f"Model '{model_name}' not loaded")

        model = self.loaded_models[model_name]
        metadata = self.model_metadata.get(model_name)

        info = {
            'model_name': model_name,
            'loaded': True,
            'input_shape': model.input_shape,
            'output_shape': model.output_shape,
            'num_parameters': model.count_params(),
            'num_layers': len(model.layers)
        }

        if metadata:
            info['metadata'] = metadata.to_dict()

        return info
