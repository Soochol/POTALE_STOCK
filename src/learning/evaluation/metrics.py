"""
Evaluation Metrics

ML 모델 성능 평가를 위한 지표 계산
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
import numpy as np
from datetime import datetime


@dataclass
class ModelPerformance:
    """모델 성능 평가 결과"""

    # Metadata
    model_name: str
    evaluation_date: datetime
    dataset_name: str
    num_samples: int

    # Overall metrics
    accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float

    # Per-class metrics
    per_class_precision: Dict[int, float] = field(default_factory=dict)
    per_class_recall: Dict[int, float] = field(default_factory=dict)
    per_class_f1: Dict[int, float] = field(default_factory=dict)
    per_class_support: Dict[int, int] = field(default_factory=dict)

    # Confusion matrix
    confusion_matrix: Optional[List[List[int]]] = None

    # Additional metrics
    weighted_precision: Optional[float] = None
    weighted_recall: Optional[float] = None
    weighted_f1: Optional[float] = None

    # Custom metadata
    notes: str = ""
    hyperparameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        result['evaluation_date'] = self.evaluation_date.isoformat()
        return result

    def get_summary(self) -> str:
        """Get human-readable summary"""
        lines = [
            f"{'='*60}",
            f"Model Performance: {self.model_name}",
            f"{'='*60}",
            f"Evaluation Date: {self.evaluation_date.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Dataset: {self.dataset_name} ({self.num_samples} samples)",
            f"",
            f"Overall Metrics:",
            f"  Accuracy:  {self.accuracy:.4f}",
            f"  Precision: {self.macro_precision:.4f} (macro)",
            f"  Recall:    {self.macro_recall:.4f} (macro)",
            f"  F1-Score:  {self.macro_f1:.4f} (macro)",
        ]

        if self.weighted_f1:
            lines.extend([
                f"",
                f"Weighted Metrics:",
                f"  Precision: {self.weighted_precision:.4f}",
                f"  Recall:    {self.weighted_recall:.4f}",
                f"  F1-Score:  {self.weighted_f1:.4f}",
            ])

        if self.per_class_f1:
            lines.append(f"\nPer-Class Metrics:")
            for class_id in sorted(self.per_class_f1.keys()):
                precision = self.per_class_precision.get(class_id, 0.0)
                recall = self.per_class_recall.get(class_id, 0.0)
                f1 = self.per_class_f1.get(class_id, 0.0)
                support = self.per_class_support.get(class_id, 0)
                lines.append(
                    f"  Class {class_id}: "
                    f"P={precision:.4f} R={recall:.4f} F1={f1:.4f} "
                    f"(n={support})"
                )

        if self.notes:
            lines.extend([f"", f"Notes: {self.notes}"])

        lines.append(f"{'='*60}")
        return "\n".join(lines)


class EvaluationMetrics:
    """ML 모델 평가 지표 계산기"""

    @staticmethod
    def calculate_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """
        정확도 계산

        Args:
            y_true: Ground truth labels
            y_pred: Predicted labels

        Returns:
            Accuracy score [0, 1]
        """
        if len(y_true) == 0:
            return 0.0

        correct = np.sum(y_true == y_pred)
        total = len(y_true)
        return float(correct / total)

    @staticmethod
    def calculate_precision(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        class_id: Optional[int] = None
    ) -> float:
        """
        정밀도 계산 (Precision = TP / (TP + FP))

        Args:
            y_true: Ground truth labels
            y_pred: Predicted labels
            class_id: Specific class (None = binary classification)

        Returns:
            Precision score [0, 1]
        """
        if class_id is None:
            # Binary classification
            true_positives = np.sum((y_true == 1) & (y_pred == 1))
            predicted_positives = np.sum(y_pred == 1)
        else:
            # Multi-class classification
            true_positives = np.sum((y_true == class_id) & (y_pred == class_id))
            predicted_positives = np.sum(y_pred == class_id)

        if predicted_positives == 0:
            return 0.0

        return float(true_positives / predicted_positives)

    @staticmethod
    def calculate_recall(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        class_id: Optional[int] = None
    ) -> float:
        """
        재현율 계산 (Recall = TP / (TP + FN))

        Args:
            y_true: Ground truth labels
            y_pred: Predicted labels
            class_id: Specific class (None = binary classification)

        Returns:
            Recall score [0, 1]
        """
        if class_id is None:
            # Binary classification
            true_positives = np.sum((y_true == 1) & (y_pred == 1))
            actual_positives = np.sum(y_true == 1)
        else:
            # Multi-class classification
            true_positives = np.sum((y_true == class_id) & (y_pred == class_id))
            actual_positives = np.sum(y_true == class_id)

        if actual_positives == 0:
            return 0.0

        return float(true_positives / actual_positives)

    @staticmethod
    def calculate_f1_score(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        class_id: Optional[int] = None
    ) -> float:
        """
        F1-Score 계산 (F1 = 2 * (P * R) / (P + R))

        Args:
            y_true: Ground truth labels
            y_pred: Predicted labels
            class_id: Specific class (None = binary classification)

        Returns:
            F1 score [0, 1]
        """
        precision = EvaluationMetrics.calculate_precision(y_true, y_pred, class_id)
        recall = EvaluationMetrics.calculate_recall(y_true, y_pred, class_id)

        if precision + recall == 0:
            return 0.0

        return float(2 * (precision * recall) / (precision + recall))

    @staticmethod
    def calculate_confusion_matrix(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        num_classes: Optional[int] = None
    ) -> np.ndarray:
        """
        Confusion Matrix 계산

        Args:
            y_true: Ground truth labels
            y_pred: Predicted labels
            num_classes: Number of classes (auto-detect if None)

        Returns:
            Confusion matrix (num_classes x num_classes)
        """
        if num_classes is None:
            num_classes = max(np.max(y_true), np.max(y_pred)) + 1

        cm = np.zeros((num_classes, num_classes), dtype=int)

        for true_label, pred_label in zip(y_true, y_pred):
            cm[true_label, pred_label] += 1

        return cm

    @staticmethod
    def calculate_macro_metrics(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        classes: Optional[List[int]] = None
    ) -> Dict[str, float]:
        """
        Macro-averaged metrics 계산

        Args:
            y_true: Ground truth labels
            y_pred: Predicted labels
            classes: List of class IDs (auto-detect if None)

        Returns:
            Dictionary with macro_precision, macro_recall, macro_f1
        """
        if classes is None:
            classes = sorted(np.unique(y_true))

        precisions = []
        recalls = []
        f1_scores = []

        for class_id in classes:
            precisions.append(
                EvaluationMetrics.calculate_precision(y_true, y_pred, class_id)
            )
            recalls.append(
                EvaluationMetrics.calculate_recall(y_true, y_pred, class_id)
            )
            f1_scores.append(
                EvaluationMetrics.calculate_f1_score(y_true, y_pred, class_id)
            )

        return {
            'macro_precision': float(np.mean(precisions)),
            'macro_recall': float(np.mean(recalls)),
            'macro_f1': float(np.mean(f1_scores))
        }

    @staticmethod
    def calculate_weighted_metrics(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        classes: Optional[List[int]] = None
    ) -> Dict[str, float]:
        """
        Weighted-averaged metrics 계산 (support로 가중평균)

        Args:
            y_true: Ground truth labels
            y_pred: Predicted labels
            classes: List of class IDs (auto-detect if None)

        Returns:
            Dictionary with weighted_precision, weighted_recall, weighted_f1
        """
        if classes is None:
            classes = sorted(np.unique(y_true))

        precisions = []
        recalls = []
        f1_scores = []
        supports = []

        for class_id in classes:
            precisions.append(
                EvaluationMetrics.calculate_precision(y_true, y_pred, class_id)
            )
            recalls.append(
                EvaluationMetrics.calculate_recall(y_true, y_pred, class_id)
            )
            f1_scores.append(
                EvaluationMetrics.calculate_f1_score(y_true, y_pred, class_id)
            )
            supports.append(int(np.sum(y_true == class_id)))

        total_support = sum(supports)

        if total_support == 0:
            return {
                'weighted_precision': 0.0,
                'weighted_recall': 0.0,
                'weighted_f1': 0.0
            }

        weights = [s / total_support for s in supports]

        return {
            'weighted_precision': float(np.average(precisions, weights=weights)),
            'weighted_recall': float(np.average(recalls, weights=weights)),
            'weighted_f1': float(np.average(f1_scores, weights=weights))
        }

    @staticmethod
    def evaluate_full(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        model_name: str,
        dataset_name: str = "test_set",
        classes: Optional[List[int]] = None,
        notes: str = "",
        hyperparameters: Optional[Dict[str, Any]] = None
    ) -> ModelPerformance:
        """
        전체 평가 지표 계산 및 ModelPerformance 생성

        Args:
            y_true: Ground truth labels
            y_pred: Predicted labels
            model_name: Model name
            dataset_name: Dataset name
            classes: List of class IDs (auto-detect if None)
            notes: Additional notes
            hyperparameters: Model hyperparameters

        Returns:
            ModelPerformance object with all metrics
        """
        if classes is None:
            classes = sorted(np.unique(y_true))

        # Overall metrics
        accuracy = EvaluationMetrics.calculate_accuracy(y_true, y_pred)
        macro_metrics = EvaluationMetrics.calculate_macro_metrics(y_true, y_pred, classes)
        weighted_metrics = EvaluationMetrics.calculate_weighted_metrics(y_true, y_pred, classes)

        # Per-class metrics
        per_class_precision = {}
        per_class_recall = {}
        per_class_f1 = {}
        per_class_support = {}

        for class_id in classes:
            per_class_precision[class_id] = EvaluationMetrics.calculate_precision(
                y_true, y_pred, class_id
            )
            per_class_recall[class_id] = EvaluationMetrics.calculate_recall(
                y_true, y_pred, class_id
            )
            per_class_f1[class_id] = EvaluationMetrics.calculate_f1_score(
                y_true, y_pred, class_id
            )
            per_class_support[class_id] = int(np.sum(y_true == class_id))

        # Confusion matrix
        cm = EvaluationMetrics.calculate_confusion_matrix(y_true, y_pred, len(classes))

        return ModelPerformance(
            model_name=model_name,
            evaluation_date=datetime.now(),
            dataset_name=dataset_name,
            num_samples=len(y_true),
            accuracy=accuracy,
            macro_precision=macro_metrics['macro_precision'],
            macro_recall=macro_metrics['macro_recall'],
            macro_f1=macro_metrics['macro_f1'],
            per_class_precision=per_class_precision,
            per_class_recall=per_class_recall,
            per_class_f1=per_class_f1,
            per_class_support=per_class_support,
            confusion_matrix=cm.tolist(),
            weighted_precision=weighted_metrics['weighted_precision'],
            weighted_recall=weighted_metrics['weighted_recall'],
            weighted_f1=weighted_metrics['weighted_f1'],
            notes=notes,
            hyperparameters=hyperparameters or {}
        )
