"""
Confusion Matrix Analysis

혼동 행렬 분석 및 시각화
"""
from typing import Dict, List, Optional, Tuple
import numpy as np
from dataclasses import dataclass


@dataclass
class ClassMetrics:
    """클래스별 세부 지표"""

    class_id: int
    class_name: str

    # Confusion matrix components
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int

    # Derived metrics
    precision: float
    recall: float
    f1_score: float
    specificity: float

    # Support
    support: int  # Actual number of samples in this class

    def get_summary(self) -> str:
        """Get human-readable summary"""
        return (
            f"Class {self.class_id} ({self.class_name}):\n"
            f"  TP={self.true_positives}, "
            f"FP={self.false_positives}, "
            f"TN={self.true_negatives}, "
            f"FN={self.false_negatives}\n"
            f"  Precision: {self.precision:.4f}\n"
            f"  Recall: {self.recall:.4f}\n"
            f"  F1-Score: {self.f1_score:.4f}\n"
            f"  Specificity: {self.specificity:.4f}\n"
            f"  Support: {self.support}"
        )


class ConfusionMatrixAnalyzer:
    """혼동 행렬 분석기"""

    def __init__(
        self,
        confusion_matrix: np.ndarray,
        class_names: Optional[Dict[int, str]] = None
    ):
        """
        Args:
            confusion_matrix: Confusion matrix (num_classes x num_classes)
            class_names: Mapping from class ID to class name
        """
        self.confusion_matrix = np.array(confusion_matrix)
        self.num_classes = self.confusion_matrix.shape[0]

        if class_names is None:
            self.class_names = {i: f"Class{i}" for i in range(self.num_classes)}
        else:
            self.class_names = class_names

        self._validate()

    def _validate(self):
        """Validate confusion matrix"""
        if len(self.confusion_matrix.shape) != 2:
            raise ValueError("Confusion matrix must be 2D")

        if self.confusion_matrix.shape[0] != self.confusion_matrix.shape[1]:
            raise ValueError("Confusion matrix must be square")

        if np.any(self.confusion_matrix < 0):
            raise ValueError("Confusion matrix values must be non-negative")

    def get_class_metrics(self, class_id: int) -> ClassMetrics:
        """
        특정 클래스의 세부 지표 계산

        Args:
            class_id: Class ID

        Returns:
            ClassMetrics object
        """
        if class_id < 0 or class_id >= self.num_classes:
            raise ValueError(f"Invalid class_id: {class_id}")

        # TP: Correctly predicted as this class
        true_positives = int(self.confusion_matrix[class_id, class_id])

        # FP: Incorrectly predicted as this class (sum of column - TP)
        false_positives = int(np.sum(self.confusion_matrix[:, class_id]) - true_positives)

        # FN: Actually this class but predicted as other (sum of row - TP)
        false_negatives = int(np.sum(self.confusion_matrix[class_id, :]) - true_positives)

        # TN: Correctly predicted as NOT this class
        true_negatives = int(
            np.sum(self.confusion_matrix) - true_positives - false_positives - false_negatives
        )

        # Support: Total actual samples in this class
        support = int(np.sum(self.confusion_matrix[class_id, :]))

        # Calculate metrics
        precision = (
            true_positives / (true_positives + false_positives)
            if (true_positives + false_positives) > 0
            else 0.0
        )

        recall = (
            true_positives / (true_positives + false_negatives)
            if (true_positives + false_negatives) > 0
            else 0.0
        )

        f1_score = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        specificity = (
            true_negatives / (true_negatives + false_positives)
            if (true_negatives + false_positives) > 0
            else 0.0
        )

        return ClassMetrics(
            class_id=class_id,
            class_name=self.class_names.get(class_id, f"Class{class_id}"),
            true_positives=true_positives,
            false_positives=false_positives,
            true_negatives=true_negatives,
            false_negatives=false_negatives,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            specificity=specificity,
            support=support
        )

    def get_all_class_metrics(self) -> List[ClassMetrics]:
        """
        모든 클래스의 세부 지표 계산

        Returns:
            List of ClassMetrics for all classes
        """
        return [
            self.get_class_metrics(class_id)
            for class_id in range(self.num_classes)
        ]

    def get_most_confused_pairs(self, top_k: int = 5) -> List[Tuple[int, int, int]]:
        """
        가장 많이 혼동되는 클래스 쌍 찾기

        Args:
            top_k: Number of top pairs to return

        Returns:
            List of (true_class, pred_class, count) tuples
        """
        confused_pairs = []

        for i in range(self.num_classes):
            for j in range(self.num_classes):
                if i != j:  # Exclude diagonal (correct predictions)
                    count = int(self.confusion_matrix[i, j])
                    if count > 0:
                        confused_pairs.append((i, j, count))

        # Sort by count (descending)
        confused_pairs.sort(key=lambda x: x[2], reverse=True)

        return confused_pairs[:top_k]

    def get_misclassification_rate(self) -> float:
        """
        전체 오분류율 계산

        Returns:
            Misclassification rate [0, 1]
        """
        total_samples = np.sum(self.confusion_matrix)
        correct_predictions = np.trace(self.confusion_matrix)

        if total_samples == 0:
            return 0.0

        return float(1.0 - (correct_predictions / total_samples))

    def get_normalized_matrix(self, normalize_by: str = 'true') -> np.ndarray:
        """
        정규화된 혼동 행렬 계산

        Args:
            normalize_by: 'true' (row-wise) or 'pred' (column-wise) or 'all'

        Returns:
            Normalized confusion matrix
        """
        cm = self.confusion_matrix.astype(float)

        if normalize_by == 'true':
            # Row-wise normalization (per true class)
            row_sums = cm.sum(axis=1, keepdims=True)
            row_sums[row_sums == 0] = 1  # Avoid division by zero
            return cm / row_sums

        elif normalize_by == 'pred':
            # Column-wise normalization (per predicted class)
            col_sums = cm.sum(axis=0, keepdims=True)
            col_sums[col_sums == 0] = 1
            return cm / col_sums

        elif normalize_by == 'all':
            # Overall normalization
            total = cm.sum()
            if total == 0:
                return cm
            return cm / total

        else:
            raise ValueError(f"Invalid normalize_by: {normalize_by}")

    def get_text_visualization(self, normalize: bool = False) -> str:
        """
        텍스트 기반 혼동 행렬 시각화

        Args:
            normalize: Whether to normalize values

        Returns:
            Text representation of confusion matrix
        """
        if normalize:
            cm = self.get_normalized_matrix(normalize_by='true')
            fmt = "{:6.2%}"
        else:
            cm = self.confusion_matrix
            fmt = "{:6d}"

        lines = []
        lines.append("\nConfusion Matrix:")
        lines.append("=" * 80)

        # Header
        header = "True\\Pred |"
        for j in range(self.num_classes):
            class_name = self.class_names.get(j, f"C{j}")
            header += f" {class_name:>8}"
        lines.append(header)
        lines.append("-" * 80)

        # Rows
        for i in range(self.num_classes):
            class_name = self.class_names.get(i, f"C{i}")
            row = f"{class_name:>9} |"

            for j in range(self.num_classes):
                if normalize:
                    row += f" {cm[i, j]:>7.1%}"
                else:
                    row += f" {cm[i, j]:>8d}"

            lines.append(row)

        lines.append("=" * 80)
        return "\n".join(lines)

    def get_summary_report(self) -> str:
        """
        전체 분석 리포트 생성

        Returns:
            Summary report text
        """
        lines = []
        lines.append("=" * 80)
        lines.append("Confusion Matrix Analysis Report")
        lines.append("=" * 80)

        # Overall statistics
        total_samples = int(np.sum(self.confusion_matrix))
        correct = int(np.trace(self.confusion_matrix))
        accuracy = correct / total_samples if total_samples > 0 else 0.0

        lines.append(f"\nOverall Statistics:")
        lines.append(f"  Total Samples: {total_samples}")
        lines.append(f"  Correct Predictions: {correct}")
        lines.append(f"  Accuracy: {accuracy:.4f}")
        lines.append(f"  Misclassification Rate: {self.get_misclassification_rate():.4f}")

        # Per-class metrics
        lines.append(f"\nPer-Class Metrics:")
        lines.append("-" * 80)

        all_metrics = self.get_all_class_metrics()
        for metrics in all_metrics:
            lines.append("")
            lines.append(metrics.get_summary())

        # Most confused pairs
        lines.append(f"\n\nMost Confused Class Pairs:")
        lines.append("-" * 80)

        confused_pairs = self.get_most_confused_pairs(top_k=5)
        for true_class, pred_class, count in confused_pairs:
            true_name = self.class_names.get(true_class, f"Class{true_class}")
            pred_name = self.class_names.get(pred_class, f"Class{pred_class}")
            lines.append(
                f"  {true_name} → {pred_name}: {count} samples"
            )

        # Confusion matrix visualization
        lines.append(f"\n")
        lines.append(self.get_text_visualization(normalize=False))

        lines.append(f"\n")
        lines.append(self.get_text_visualization(normalize=True))

        lines.append("=" * 80)
        return "\n".join(lines)
