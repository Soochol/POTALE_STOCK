"""
Tests for Evaluation Metrics

평가 지표 계산 테스트
"""
import pytest
import numpy as np
from datetime import datetime

from src.learning.evaluation.metrics import (
    EvaluationMetrics,
    ModelPerformance
)


@pytest.mark.unit
class TestEvaluationMetrics:
    """EvaluationMetrics 클래스 테스트"""

    def test_accuracy_perfect(self):
        """완벽한 정확도 테스트"""
        y_true = np.array([0, 1, 2, 0, 1, 2])
        y_pred = np.array([0, 1, 2, 0, 1, 2])

        accuracy = EvaluationMetrics.calculate_accuracy(y_true, y_pred)

        assert accuracy == 1.0

    def test_accuracy_zero(self):
        """0% 정확도 테스트"""
        y_true = np.array([0, 0, 0])
        y_pred = np.array([1, 1, 1])

        accuracy = EvaluationMetrics.calculate_accuracy(y_true, y_pred)

        assert accuracy == 0.0

    def test_accuracy_partial(self):
        """부분 정확도 테스트"""
        y_true = np.array([0, 1, 2, 0, 1, 2])
        y_pred = np.array([0, 1, 0, 0, 2, 2])  # 4/6 correct

        accuracy = EvaluationMetrics.calculate_accuracy(y_true, y_pred)

        assert abs(accuracy - 0.666667) < 0.001

    def test_accuracy_empty(self):
        """빈 배열 정확도 테스트"""
        y_true = np.array([])
        y_pred = np.array([])

        accuracy = EvaluationMetrics.calculate_accuracy(y_true, y_pred)

        assert accuracy == 0.0

    def test_precision_binary_perfect(self):
        """이진 분류 완벽한 정밀도"""
        y_true = np.array([0, 1, 1, 0, 1])
        y_pred = np.array([0, 1, 1, 0, 1])

        precision = EvaluationMetrics.calculate_precision(y_true, y_pred)

        assert precision == 1.0

    def test_precision_binary_partial(self):
        """이진 분류 부분 정밀도"""
        y_true = np.array([0, 0, 1, 1, 1])
        y_pred = np.array([0, 1, 1, 1, 0])  # 2 TP, 1 FP → 2/3

        precision = EvaluationMetrics.calculate_precision(y_true, y_pred)

        assert abs(precision - 0.666667) < 0.001

    def test_precision_no_positive_predictions(self):
        """양성 예측이 없을 때"""
        y_true = np.array([0, 1, 1])
        y_pred = np.array([0, 0, 0])

        precision = EvaluationMetrics.calculate_precision(y_true, y_pred)

        assert precision == 0.0

    def test_precision_multiclass(self):
        """다중 클래스 정밀도"""
        y_true = np.array([0, 1, 2, 0, 1, 2])
        y_pred = np.array([0, 1, 0, 0, 2, 2])

        # Class 0: TP=2, FP=1 → 2/3
        precision_0 = EvaluationMetrics.calculate_precision(y_true, y_pred, class_id=0)
        assert abs(precision_0 - 0.666667) < 0.001

        # Class 1: TP=1, FP=0 → 1/1
        precision_1 = EvaluationMetrics.calculate_precision(y_true, y_pred, class_id=1)
        assert precision_1 == 1.0

        # Class 2: TP=1, FP=1 → 1/2
        precision_2 = EvaluationMetrics.calculate_precision(y_true, y_pred, class_id=2)
        assert precision_2 == 0.5

    def test_recall_binary_perfect(self):
        """이진 분류 완벽한 재현율"""
        y_true = np.array([0, 1, 1, 0, 1])
        y_pred = np.array([0, 1, 1, 0, 1])

        recall = EvaluationMetrics.calculate_recall(y_true, y_pred)

        assert recall == 1.0

    def test_recall_binary_partial(self):
        """이진 분류 부분 재현율"""
        y_true = np.array([0, 0, 1, 1, 1])
        y_pred = np.array([0, 1, 1, 1, 0])  # 2 TP, 1 FN → 2/3

        recall = EvaluationMetrics.calculate_recall(y_true, y_pred)

        assert abs(recall - 0.666667) < 0.001

    def test_recall_no_actual_positives(self):
        """실제 양성이 없을 때"""
        y_true = np.array([0, 0, 0])
        y_pred = np.array([1, 1, 1])

        recall = EvaluationMetrics.calculate_recall(y_true, y_pred)

        assert recall == 0.0

    def test_recall_multiclass(self):
        """다중 클래스 재현율"""
        y_true = np.array([0, 1, 2, 0, 1, 2])
        y_pred = np.array([0, 1, 0, 0, 2, 2])

        # Class 0: TP=2, FN=0 → 2/2
        recall_0 = EvaluationMetrics.calculate_recall(y_true, y_pred, class_id=0)
        assert recall_0 == 1.0

        # Class 1: TP=1, FN=1 → 1/2
        recall_1 = EvaluationMetrics.calculate_recall(y_true, y_pred, class_id=1)
        assert recall_1 == 0.5

        # Class 2: TP=1, FN=1 → 1/2
        recall_2 = EvaluationMetrics.calculate_recall(y_true, y_pred, class_id=2)
        assert recall_2 == 0.5

    def test_f1_score_perfect(self):
        """완벽한 F1 스코어"""
        y_true = np.array([0, 1, 1, 0, 1])
        y_pred = np.array([0, 1, 1, 0, 1])

        f1 = EvaluationMetrics.calculate_f1_score(y_true, y_pred)

        assert f1 == 1.0

    def test_f1_score_zero(self):
        """F1 스코어 0 (precision과 recall 모두 0)"""
        y_true = np.array([0, 0, 0])
        y_pred = np.array([1, 1, 1])

        f1 = EvaluationMetrics.calculate_f1_score(y_true, y_pred)

        assert f1 == 0.0

    def test_f1_score_calculation(self):
        """F1 스코어 계산 검증"""
        y_true = np.array([0, 0, 1, 1, 1])
        y_pred = np.array([0, 1, 1, 1, 0])

        # Precision = 2/3, Recall = 2/3
        # F1 = 2 * (2/3 * 2/3) / (2/3 + 2/3) = 2/3
        f1 = EvaluationMetrics.calculate_f1_score(y_true, y_pred)

        assert abs(f1 - 0.666667) < 0.001

    def test_confusion_matrix_binary(self):
        """이진 분류 혼동 행렬"""
        y_true = np.array([0, 1, 0, 1])
        y_pred = np.array([0, 1, 1, 0])

        cm = EvaluationMetrics.calculate_confusion_matrix(y_true, y_pred)

        expected = np.array([
            [1, 1],  # True 0: 1 correct, 1 misclassified as 1
            [1, 1]   # True 1: 1 misclassified as 0, 1 correct
        ])

        np.testing.assert_array_equal(cm, expected)

    def test_confusion_matrix_multiclass(self):
        """다중 클래스 혼동 행렬"""
        y_true = np.array([0, 1, 2, 0, 1, 2])
        y_pred = np.array([0, 1, 0, 0, 2, 2])

        cm = EvaluationMetrics.calculate_confusion_matrix(y_true, y_pred)

        expected = np.array([
            [2, 0, 0],  # True 0
            [0, 1, 1],  # True 1
            [1, 0, 1]   # True 2
        ])

        np.testing.assert_array_equal(cm, expected)

    def test_confusion_matrix_auto_detect_classes(self):
        """클래스 개수 자동 감지"""
        y_true = np.array([0, 1, 2])
        y_pred = np.array([0, 1, 2])

        cm = EvaluationMetrics.calculate_confusion_matrix(y_true, y_pred)

        assert cm.shape == (3, 3)

    def test_macro_metrics(self):
        """Macro-averaged 지표 계산"""
        y_true = np.array([0, 1, 2, 0, 1, 2])
        y_pred = np.array([0, 1, 0, 0, 2, 2])

        macro = EvaluationMetrics.calculate_macro_metrics(y_true, y_pred)

        # Class 0: P=0.667, R=1.0, F1=0.8
        # Class 1: P=1.0, R=0.5, F1=0.667
        # Class 2: P=0.5, R=0.5, F1=0.5
        # Macro: P=0.722, R=0.667, F1=0.656

        assert 'macro_precision' in macro
        assert 'macro_recall' in macro
        assert 'macro_f1' in macro

        assert abs(macro['macro_precision'] - 0.722222) < 0.001
        assert abs(macro['macro_recall'] - 0.666667) < 0.001
        assert abs(macro['macro_f1'] - 0.655556) < 0.001

    def test_weighted_metrics(self):
        """Weighted-averaged 지표 계산"""
        # Imbalanced dataset
        y_true = np.array([0, 0, 0, 0, 1, 2])  # Class 0 dominant
        y_pred = np.array([0, 0, 0, 1, 1, 2])

        weighted = EvaluationMetrics.calculate_weighted_metrics(y_true, y_pred)

        assert 'weighted_precision' in weighted
        assert 'weighted_recall' in weighted
        assert 'weighted_f1' in weighted

        # Class 0 has more weight (4/6) than others (1/6 each)
        assert weighted['weighted_precision'] > 0
        assert weighted['weighted_recall'] > 0
        assert weighted['weighted_f1'] > 0

    def test_weighted_metrics_empty_classes(self):
        """빈 클래스가 있을 때 가중 평균"""
        y_true = np.array([])
        y_pred = np.array([])

        weighted = EvaluationMetrics.calculate_weighted_metrics(y_true, y_pred, classes=[0, 1])

        assert weighted['weighted_precision'] == 0.0
        assert weighted['weighted_recall'] == 0.0
        assert weighted['weighted_f1'] == 0.0

    def test_evaluate_full(self):
        """전체 평가 통합 테스트"""
        y_true = np.array([0, 1, 2, 0, 1, 2, 0, 1, 2])
        y_pred = np.array([0, 1, 0, 0, 2, 2, 1, 1, 2])

        performance = EvaluationMetrics.evaluate_full(
            y_true=y_true,
            y_pred=y_pred,
            model_name="TestModel",
            dataset_name="test_data",
            classes=[0, 1, 2],
            notes="Test evaluation",
            hyperparameters={'learning_rate': 0.001}
        )

        # Check metadata
        assert performance.model_name == "TestModel"
        assert performance.dataset_name == "test_data"
        assert performance.num_samples == 9
        assert performance.notes == "Test evaluation"
        assert performance.hyperparameters['learning_rate'] == 0.001

        # Check overall metrics
        assert 0 <= performance.accuracy <= 1
        assert 0 <= performance.macro_precision <= 1
        assert 0 <= performance.macro_recall <= 1
        assert 0 <= performance.macro_f1 <= 1

        # Check per-class metrics
        assert len(performance.per_class_precision) == 3
        assert len(performance.per_class_recall) == 3
        assert len(performance.per_class_f1) == 3
        assert len(performance.per_class_support) == 3

        # Check confusion matrix
        assert performance.confusion_matrix is not None
        assert len(performance.confusion_matrix) == 3

        # Check weighted metrics
        assert performance.weighted_precision is not None
        assert performance.weighted_recall is not None
        assert performance.weighted_f1 is not None


@pytest.mark.unit
class TestModelPerformance:
    """ModelPerformance 클래스 테스트"""

    def test_model_performance_creation(self):
        """ModelPerformance 생성 테스트"""
        performance = ModelPerformance(
            model_name="TestModel",
            evaluation_date=datetime.now(),
            dataset_name="test_set",
            num_samples=100,
            accuracy=0.85,
            macro_precision=0.80,
            macro_recall=0.75,
            macro_f1=0.77,
            per_class_precision={0: 0.9, 1: 0.7},
            per_class_recall={0: 0.8, 1: 0.7},
            per_class_f1={0: 0.85, 1: 0.7},
            per_class_support={0: 60, 1: 40}
        )

        assert performance.model_name == "TestModel"
        assert performance.num_samples == 100
        assert performance.accuracy == 0.85

    def test_to_dict(self):
        """Dictionary 변환 테스트"""
        performance = ModelPerformance(
            model_name="TestModel",
            evaluation_date=datetime(2024, 1, 1, 12, 0, 0),
            dataset_name="test_set",
            num_samples=100,
            accuracy=0.85,
            macro_precision=0.80,
            macro_recall=0.75,
            macro_f1=0.77
        )

        result = performance.to_dict()

        assert result['model_name'] == "TestModel"
        assert result['evaluation_date'] == "2024-01-01T12:00:00"
        assert result['accuracy'] == 0.85

    def test_get_summary(self):
        """요약 문자열 생성 테스트"""
        performance = ModelPerformance(
            model_name="TestModel",
            evaluation_date=datetime.now(),
            dataset_name="test_set",
            num_samples=100,
            accuracy=0.85,
            macro_precision=0.80,
            macro_recall=0.75,
            macro_f1=0.77,
            per_class_precision={0: 0.9, 1: 0.7},
            per_class_recall={0: 0.8, 1: 0.7},
            per_class_f1={0: 0.85, 1: 0.7},
            per_class_support={0: 60, 1: 40},
            notes="Test evaluation"
        )

        summary = performance.get_summary()

        assert "TestModel" in summary
        assert "Accuracy" in summary
        assert "0.8500" in summary
        assert "Test evaluation" in summary
        assert "Class 0" in summary
        assert "Class 1" in summary

    def test_get_summary_with_weighted_metrics(self):
        """가중 평균 포함 요약"""
        performance = ModelPerformance(
            model_name="TestModel",
            evaluation_date=datetime.now(),
            dataset_name="test_set",
            num_samples=100,
            accuracy=0.85,
            macro_precision=0.80,
            macro_recall=0.75,
            macro_f1=0.77,
            weighted_precision=0.82,
            weighted_recall=0.76,
            weighted_f1=0.79
        )

        summary = performance.get_summary()

        assert "Weighted Metrics" in summary
        assert "0.8200" in summary  # weighted_precision
