"""
Realtime Predictor

실시간 단일 예측
"""
from typing import Optional
import numpy as np
from datetime import datetime
import tensorflow as tf

from src.learning.inference.prediction_result import PredictionResult
from src.learning.inference.model_deployer import ModelDeployer


class RealtimePredictor:
    """실시간 예측 실행기"""

    def __init__(self, deployer: ModelDeployer):
        """
        Args:
            deployer: ModelDeployer instance
        """
        self.deployer = deployer

    def predict_single(
        self,
        model_name: str,
        features: np.ndarray,
        ticker: str,
        start_date: datetime,
        end_date: datetime
    ) -> PredictionResult:
        """
        Run single prediction

        Args:
            model_name: Model identifier
            features: Feature array (sequence_length, num_features)
            ticker: Stock ticker
            start_date: Period start date
            end_date: Period end date

        Returns:
            PredictionResult

        Raises:
            ValueError: If model not loaded or invalid input
        """
        # Load model
        model = self.deployer.get_model(model_name)
        if model is None:
            model = self.deployer.load_model(model_name)

        metadata = self.deployer.get_metadata(model_name)

        # Ensure features have batch dimension
        if len(features.shape) == 2:
            features = np.expand_dims(features, axis=0)

        # Predict
        probs = model.predict(features, verbose=0)[0]

        predicted_class = int(np.argmax(probs))
        confidence = float(probs[predicted_class])

        return PredictionResult(
            ticker=ticker,
            started_at=start_date,
            ended_at=end_date,
            predicted_class=predicted_class,
            confidence_score=confidence,
            class_probabilities={
                class_id: float(prob)
                for class_id, prob in enumerate(probs)
            },
            model_name=model_name,
            model_version=metadata.version if metadata else "unknown",
            architecture_type=metadata.architecture_type if metadata else "unknown",
            num_features=features.shape[-1]
        )

    def predict_with_threshold(
        self,
        model_name: str,
        features: np.ndarray,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        min_confidence: float = 0.7
    ) -> Optional[PredictionResult]:
        """
        Run single prediction with confidence threshold

        Args:
            model_name: Model identifier
            features: Feature array
            ticker: Stock ticker
            start_date: Period start date
            end_date: Period end date
            min_confidence: Minimum confidence threshold

        Returns:
            PredictionResult if confidence >= threshold, None otherwise
        """
        result = self.predict_single(
            model_name=model_name,
            features=features,
            ticker=ticker,
            start_date=start_date,
            end_date=end_date
        )

        if result.confidence_score >= min_confidence:
            return result
        else:
            return None
