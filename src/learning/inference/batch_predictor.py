"""
Batch Predictor

대량 데이터에 대한 배치 예측
"""
from typing import List, Optional
import time
import numpy as np
from datetime import datetime
import tensorflow as tf

from src.learning.inference.prediction_result import PredictionResult, BatchPredictionResult
from src.learning.inference.model_deployer import ModelDeployer


class BatchPredictor:
    """배치 예측 실행기"""

    def __init__(self, deployer: ModelDeployer):
        """
        Args:
            deployer: ModelDeployer instance
        """
        self.deployer = deployer

    def predict_batch(
        self,
        model_name: str,
        features: np.ndarray,
        tickers: List[str],
        dates: List[tuple],  # List of (start_date, end_date)
        batch_size: int = 32
    ) -> BatchPredictionResult:
        """
        Run batch prediction

        Args:
            model_name: Model identifier
            features: Feature array (num_samples, sequence_length, num_features)
            tickers: List of tickers
            dates: List of (start_date, end_date) tuples
            batch_size: Batch size for prediction

        Returns:
            BatchPredictionResult

        Raises:
            ValueError: If model not loaded or input shapes mismatch
        """
        start_time = time.time()

        # Load model
        model = self.deployer.get_model(model_name)
        if model is None:
            model = self.deployer.load_model(model_name)

        metadata = self.deployer.get_metadata(model_name)

        # Validate inputs
        if len(tickers) != len(features) or len(tickers) != len(dates):
            raise ValueError("tickers, features, and dates must have same length")

        # Initialize result
        result = BatchPredictionResult(
            model_name=model_name,
            batch_date=datetime.now()
        )

        # Run predictions
        try:
            # Predict in batches
            predictions = model.predict(features, batch_size=batch_size, verbose=0)

            # Process results
            for idx, (ticker, (start_date, end_date), probs) in enumerate(
                zip(tickers, dates, predictions)
            ):
                try:
                    predicted_class = int(np.argmax(probs))
                    confidence = float(probs[predicted_class])

                    prediction = PredictionResult(
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
                        num_features=features.shape[-1] if len(features.shape) > 1 else 0
                    )

                    result.add_prediction(prediction)

                except Exception as e:
                    result.add_error(
                        ticker=ticker,
                        error=str(e),
                        details={'index': idx}
                    )

        except Exception as e:
            # Global error
            for ticker in tickers:
                result.add_error(
                    ticker=ticker,
                    error=f"Batch prediction failed: {str(e)}"
                )

        result.processing_time_seconds = time.time() - start_time

        return result

    def predict_with_confidence_filter(
        self,
        model_name: str,
        features: np.ndarray,
        tickers: List[str],
        dates: List[tuple],
        min_confidence: float = 0.7,
        batch_size: int = 32
    ) -> BatchPredictionResult:
        """
        Run batch prediction and filter by confidence

        Args:
            model_name: Model identifier
            features: Feature array
            tickers: List of tickers
            dates: List of (start_date, end_date) tuples
            min_confidence: Minimum confidence threshold
            batch_size: Batch size for prediction

        Returns:
            BatchPredictionResult with filtered predictions
        """
        result = self.predict_batch(
            model_name=model_name,
            features=features,
            tickers=tickers,
            dates=dates,
            batch_size=batch_size
        )

        # Filter by confidence
        filtered_predictions = [
            p for p in result.predictions
            if p.confidence_score >= min_confidence
        ]

        # Update result
        result.predictions = filtered_predictions
        result.successful_predictions = len(filtered_predictions)
        result._update_stats()

        return result
