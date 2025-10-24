"""
Prediction Result

모델 예측 결과 데이터 구조
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
import numpy as np


@dataclass
class PredictionResult:
    """모델 예측 결과"""

    # Input data
    ticker: str
    started_at: datetime
    ended_at: datetime

    # Prediction
    predicted_class: int
    confidence_score: float
    class_probabilities: Dict[int, float] = field(default_factory=dict)

    # Model info
    model_name: str = ""
    model_version: str = ""
    architecture_type: str = ""

    # Metadata
    prediction_date: datetime = field(default_factory=datetime.now)
    features_used: List[str] = field(default_factory=list)
    num_features: int = 0

    # Additional info
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        result['started_at'] = self.started_at.isoformat()
        result['ended_at'] = self.ended_at.isoformat()
        result['prediction_date'] = self.prediction_date.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PredictionResult':
        """Create from dictionary"""
        data = data.copy()
        data['started_at'] = datetime.fromisoformat(data['started_at'])
        data['ended_at'] = datetime.fromisoformat(data['ended_at'])
        data['prediction_date'] = datetime.fromisoformat(data['prediction_date'])
        return cls(**data)

    def get_top_k_classes(self, k: int = 3) -> List[tuple]:
        """
        Get top K predicted classes

        Args:
            k: Number of top classes

        Returns:
            List of (class_id, probability) tuples sorted by probability
        """
        sorted_probs = sorted(
            self.class_probabilities.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_probs[:k]

    def is_confident(self, threshold: float = 0.7) -> bool:
        """
        Check if prediction is confident

        Args:
            threshold: Confidence threshold

        Returns:
            True if confidence >= threshold
        """
        return self.confidence_score >= threshold


@dataclass
class BatchPredictionResult:
    """배치 예측 결과"""

    predictions: List[PredictionResult] = field(default_factory=list)
    total_predictions: int = 0
    successful_predictions: int = 0
    failed_predictions: int = 0
    average_confidence: float = 0.0
    processing_time_seconds: float = 0.0

    # Model info
    model_name: str = ""
    batch_date: datetime = field(default_factory=datetime.now)

    # Errors
    errors: List[Dict[str, Any]] = field(default_factory=list)

    def add_prediction(self, prediction: PredictionResult):
        """Add prediction result"""
        self.predictions.append(prediction)
        self.successful_predictions += 1
        self.total_predictions = len(self.predictions)
        self._update_stats()

    def add_error(self, ticker: str, error: str, details: Optional[Dict[str, Any]] = None):
        """Add error"""
        self.errors.append({
            'ticker': ticker,
            'error': error,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        })
        self.failed_predictions += 1

    def _update_stats(self):
        """Update aggregate statistics"""
        if self.predictions:
            confidences = [p.confidence_score for p in self.predictions]
            self.average_confidence = float(np.mean(confidences))

    def get_summary(self) -> str:
        """Get human-readable summary"""
        lines = [
            f"{'='*60}",
            f"Batch Prediction Summary",
            f"{'='*60}",
            f"Model: {self.model_name}",
            f"Batch Date: {self.batch_date.strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"Results:",
            f"  Total Predictions: {self.total_predictions}",
            f"  Successful: {self.successful_predictions}",
            f"  Failed: {self.failed_predictions}",
            f"  Average Confidence: {self.average_confidence:.4f}",
            f"  Processing Time: {self.processing_time_seconds:.2f}s",
        ]

        if self.errors:
            lines.append(f"\nErrors ({len(self.errors)}):")
            for error in self.errors[:5]:  # Show first 5 errors
                lines.append(f"  {error['ticker']}: {error['error']}")
            if len(self.errors) > 5:
                lines.append(f"  ... and {len(self.errors) - 5} more")

        lines.append(f"{'='*60}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'predictions': [p.to_dict() for p in self.predictions],
            'total_predictions': self.total_predictions,
            'successful_predictions': self.successful_predictions,
            'failed_predictions': self.failed_predictions,
            'average_confidence': self.average_confidence,
            'processing_time_seconds': self.processing_time_seconds,
            'model_name': self.model_name,
            'batch_date': self.batch_date.isoformat(),
            'errors': self.errors
        }
