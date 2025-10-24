"""
Tests for Confusion Matrix Analyzer

혼동 행렬 분석 테스트
"""
import pytest
import numpy as np

from src.learning.evaluation.confusion_matrix import (
    ClassMetrics,
    ConfusionMatrixAnalyzer
)


@pytest.mark.unit
class TestConfusionMatrixAnalyzer:
    """ConfusionMatrixAnalyzer 테스트"""

    def test_initialization(self):
        """초기화 테스트"""
        cm = np.array([
            [10, 2],
            [3, 15]
        ])

        analyzer = ConfusionMatrixAnalyzer(cm)

        assert analyzer.num_classes == 2
        np.testing.assert_array_equal(analyzer.confusion_matrix, cm)

    def test_initialization_with_class_names(self):
        """클래스 이름과 함께 초기화"""
        cm = np.array([[10, 2], [3, 15]])
        class_names = {0: "Negative", 1: "Positive"}

        analyzer = ConfusionMatrixAnalyzer(cm, class_names)

        assert analyzer.class_names[0] == "Negative"
        assert analyzer.class_names[1] == "Positive"

    def test_initialization_default_class_names(self):
        """기본 클래스 이름"""
        cm = np.array([[10, 2], [3, 15]])

        analyzer = ConfusionMatrixAnalyzer(cm)

        assert analyzer.class_names[0] == "Class0"
        assert analyzer.class_names[1] == "Class1"

    def test_validate_non_square_matrix(self):
        """비정방 행렬 검증 실패"""
        cm = np.array([[10, 2, 1], [3, 15, 2]])

        with pytest.raises(ValueError, match="must be square"):
            ConfusionMatrixAnalyzer(cm)

    def test_validate_negative_values(self):
        """음수 값 검증 실패"""
        cm = np.array([[10, -2], [3, 15]])

        with pytest.raises(ValueError, match="must be non-negative"):
            ConfusionMatrixAnalyzer(cm)

    def test_validate_not_2d(self):
        """1D 배열 검증 실패"""
        cm = np.array([10, 2, 3, 15])

        with pytest.raises(ValueError, match="must be 2D"):
            ConfusionMatrixAnalyzer(cm)

    def test_get_class_metrics_binary(self):
        """이진 분류 클래스 지표"""
        # Class 0: TP=10, FP=3, FN=2, TN=15
        # Class 1: TP=15, FP=2, FN=3, TN=10
        cm = np.array([
            [10, 2],
            [3, 15]
        ])

        analyzer = ConfusionMatrixAnalyzer(cm)
        metrics = analyzer.get_class_metrics(class_id=0)

        assert metrics.true_positives == 10
        assert metrics.false_positives == 3
        assert metrics.false_negatives == 2
        assert metrics.true_negatives == 15

        # Precision = TP / (TP + FP) = 10 / 13
        assert abs(metrics.precision - 10/13) < 0.001

        # Recall = TP / (TP + FN) = 10 / 12
        assert abs(metrics.recall - 10/12) < 0.001

        # F1 = 2 * P * R / (P + R)
        expected_f1 = 2 * (10/13) * (10/12) / ((10/13) + (10/12))
        assert abs(metrics.f1_score - expected_f1) < 0.001

        # Specificity = TN / (TN + FP) = 15 / 18
        assert abs(metrics.specificity - 15/18) < 0.001

        assert metrics.support == 12  # TP + FN

    def test_get_class_metrics_multiclass(self):
        """다중 클래스 지표"""
        cm = np.array([
            [10, 2, 1],
            [3, 15, 2],
            [1, 1, 8]
        ])

        analyzer = ConfusionMatrixAnalyzer(cm)

        # Class 0
        metrics_0 = analyzer.get_class_metrics(class_id=0)
        assert metrics_0.true_positives == 10
        assert metrics_0.support == 13  # 10 + 2 + 1

        # Class 1
        metrics_1 = analyzer.get_class_metrics(class_id=1)
        assert metrics_1.true_positives == 15
        assert metrics_1.support == 20  # 3 + 15 + 2

        # Class 2
        metrics_2 = analyzer.get_class_metrics(class_id=2)
        assert metrics_2.true_positives == 8
        assert metrics_2.support == 10  # 1 + 1 + 8

    def test_get_class_metrics_perfect_classifier(self):
        """완벽한 분류기 지표"""
        cm = np.array([
            [10, 0],
            [0, 15]
        ])

        analyzer = ConfusionMatrixAnalyzer(cm)
        metrics = analyzer.get_class_metrics(class_id=0)

        assert metrics.precision == 1.0
        assert metrics.recall == 1.0
        assert metrics.f1_score == 1.0
        assert metrics.specificity == 1.0

    def test_get_class_metrics_no_predictions(self):
        """예측이 없는 클래스"""
        cm = np.array([
            [10, 5],
            [0, 0]
        ])

        analyzer = ConfusionMatrixAnalyzer(cm)
        metrics = analyzer.get_class_metrics(class_id=1)

        # TP=0, FP=5, FN=0, TN=10
        assert metrics.true_positives == 0
        assert metrics.precision == 0.0
        # Recall is undefined (0/0), should return 0
        assert metrics.recall == 0.0

    def test_get_class_metrics_invalid_class_id(self):
        """잘못된 클래스 ID"""
        cm = np.array([[10, 2], [3, 15]])
        analyzer = ConfusionMatrixAnalyzer(cm)

        with pytest.raises(ValueError, match="Invalid class_id"):
            analyzer.get_class_metrics(class_id=5)

        with pytest.raises(ValueError, match="Invalid class_id"):
            analyzer.get_class_metrics(class_id=-1)

    def test_get_all_class_metrics(self):
        """모든 클래스 지표"""
        cm = np.array([
            [10, 2, 1],
            [3, 15, 2],
            [1, 1, 8]
        ])

        analyzer = ConfusionMatrixAnalyzer(cm)
        all_metrics = analyzer.get_all_class_metrics()

        assert len(all_metrics) == 3
        assert all_metrics[0].class_id == 0
        assert all_metrics[1].class_id == 1
        assert all_metrics[2].class_id == 2

    def test_get_most_confused_pairs(self):
        """가장 혼동되는 클래스 쌍"""
        cm = np.array([
            [10, 5, 1],  # Class 0 → Class 1 (5 times)
            [2, 15, 8],  # Class 1 → Class 2 (8 times)
            [3, 1, 20]   # Class 2 → Class 0 (3 times)
        ])

        analyzer = ConfusionMatrixAnalyzer(cm)
        confused_pairs = analyzer.get_most_confused_pairs(top_k=3)

        # Top 3: (1→2, 8), (0→1, 5), (2→0, 3)
        assert confused_pairs[0] == (1, 2, 8)
        assert confused_pairs[1] == (0, 1, 5)
        assert confused_pairs[2] == (2, 0, 3)

    def test_get_most_confused_pairs_perfect_classifier(self):
        """완벽한 분류기 (혼동 없음)"""
        cm = np.array([
            [10, 0, 0],
            [0, 15, 0],
            [0, 0, 20]
        ])

        analyzer = ConfusionMatrixAnalyzer(cm)
        confused_pairs = analyzer.get_most_confused_pairs(top_k=5)

        assert len(confused_pairs) == 0

    def test_get_most_confused_pairs_top_k(self):
        """Top K 제한"""
        cm = np.array([
            [10, 5, 1, 2],
            [2, 15, 8, 1],
            [3, 1, 20, 4],
            [1, 2, 3, 25]
        ])

        analyzer = ConfusionMatrixAnalyzer(cm)
        confused_pairs = analyzer.get_most_confused_pairs(top_k=2)

        assert len(confused_pairs) == 2

    def test_get_misclassification_rate(self):
        """오분류율 계산"""
        cm = np.array([
            [10, 2],
            [3, 15]
        ])

        analyzer = ConfusionMatrixAnalyzer(cm)
        misclass_rate = analyzer.get_misclassification_rate()

        # Total: 30, Correct: 25, Misclassified: 5
        # Rate: 5/30 = 0.1667
        assert abs(misclass_rate - 5/30) < 0.001

    def test_get_misclassification_rate_perfect(self):
        """완벽한 분류기 오분류율"""
        cm = np.array([
            [10, 0],
            [0, 15]
        ])

        analyzer = ConfusionMatrixAnalyzer(cm)
        misclass_rate = analyzer.get_misclassification_rate()

        assert misclass_rate == 0.0

    def test_get_misclassification_rate_empty(self):
        """빈 혼동 행렬"""
        cm = np.array([
            [0, 0],
            [0, 0]
        ])

        analyzer = ConfusionMatrixAnalyzer(cm)
        misclass_rate = analyzer.get_misclassification_rate()

        assert misclass_rate == 0.0

    def test_get_normalized_matrix_by_true(self):
        """행 정규화 (True 클래스 기준)"""
        cm = np.array([
            [10, 5],
            [2, 8]
        ])

        analyzer = ConfusionMatrixAnalyzer(cm)
        normalized = analyzer.get_normalized_matrix(normalize_by='true')

        # Row 0: [10/15, 5/15] = [0.667, 0.333]
        # Row 1: [2/10, 8/10] = [0.2, 0.8]
        expected = np.array([
            [10/15, 5/15],
            [2/10, 8/10]
        ])

        np.testing.assert_array_almost_equal(normalized, expected, decimal=3)

    def test_get_normalized_matrix_by_pred(self):
        """열 정규화 (Predicted 클래스 기준)"""
        cm = np.array([
            [10, 5],
            [2, 8]
        ])

        analyzer = ConfusionMatrixAnalyzer(cm)
        normalized = analyzer.get_normalized_matrix(normalize_by='pred')

        # Col 0: [10/12, 2/12]
        # Col 1: [5/13, 8/13]
        expected = np.array([
            [10/12, 5/13],
            [2/12, 8/13]
        ])

        np.testing.assert_array_almost_equal(normalized, expected, decimal=3)

    def test_get_normalized_matrix_by_all(self):
        """전체 정규화"""
        cm = np.array([
            [10, 5],
            [2, 8]
        ])

        analyzer = ConfusionMatrixAnalyzer(cm)
        normalized = analyzer.get_normalized_matrix(normalize_by='all')

        # Total: 25
        expected = np.array([
            [10/25, 5/25],
            [2/25, 8/25]
        ])

        np.testing.assert_array_almost_equal(normalized, expected, decimal=3)

    def test_get_normalized_matrix_invalid_method(self):
        """잘못된 정규화 방법"""
        cm = np.array([[10, 5], [2, 8]])
        analyzer = ConfusionMatrixAnalyzer(cm)

        with pytest.raises(ValueError, match="Invalid normalize_by"):
            analyzer.get_normalized_matrix(normalize_by='invalid')

    def test_get_normalized_matrix_zero_row(self):
        """0인 행 처리 (division by zero 방지)"""
        cm = np.array([
            [10, 5],
            [0, 0]
        ])

        analyzer = ConfusionMatrixAnalyzer(cm)
        normalized = analyzer.get_normalized_matrix(normalize_by='true')

        # Row 0: [10/15, 5/15]
        # Row 1: [0/1, 0/1] = [0, 0] (avoid division by zero)
        expected = np.array([
            [10/15, 5/15],
            [0, 0]
        ])

        np.testing.assert_array_almost_equal(normalized, expected, decimal=3)

    def test_get_text_visualization(self):
        """텍스트 시각화"""
        cm = np.array([
            [10, 2],
            [3, 15]
        ])

        class_names = {0: "Cat", 1: "Dog"}
        analyzer = ConfusionMatrixAnalyzer(cm, class_names)

        text = analyzer.get_text_visualization(normalize=False)

        assert "Confusion Matrix" in text
        assert "Cat" in text
        assert "Dog" in text
        assert "10" in text
        assert "15" in text

    def test_get_text_visualization_normalized(self):
        """정규화된 텍스트 시각화"""
        cm = np.array([
            [10, 5],
            [2, 8]
        ])

        analyzer = ConfusionMatrixAnalyzer(cm)
        text = analyzer.get_text_visualization(normalize=True)

        assert "%" in text  # Percentage format

    def test_get_summary_report(self):
        """전체 요약 리포트"""
        cm = np.array([
            [10, 2, 1],
            [3, 15, 2],
            [1, 1, 8]
        ])

        class_names = {0: "Block1", 1: "Block2", 2: "Block3"}
        analyzer = ConfusionMatrixAnalyzer(cm, class_names)

        report = analyzer.get_summary_report()

        # Check sections
        assert "Confusion Matrix Analysis Report" in report
        assert "Overall Statistics" in report
        assert "Per-Class Metrics" in report
        assert "Most Confused Class Pairs" in report
        assert "Block1" in report
        assert "Block2" in report
        assert "Block3" in report

        # Check metrics present
        assert "Accuracy" in report
        assert "Precision" in report
        assert "Recall" in report
        assert "F1-Score" in report


@pytest.mark.unit
class TestClassMetrics:
    """ClassMetrics 테스트"""

    def test_class_metrics_creation(self):
        """ClassMetrics 생성"""
        metrics = ClassMetrics(
            class_id=0,
            class_name="Block1",
            true_positives=10,
            false_positives=3,
            true_negatives=15,
            false_negatives=2,
            precision=0.769,
            recall=0.833,
            f1_score=0.800,
            specificity=0.833,
            support=12
        )

        assert metrics.class_id == 0
        assert metrics.class_name == "Block1"
        assert metrics.true_positives == 10
        assert metrics.support == 12

    def test_class_metrics_summary(self):
        """ClassMetrics 요약"""
        metrics = ClassMetrics(
            class_id=1,
            class_name="Block2",
            true_positives=15,
            false_positives=5,
            true_negatives=20,
            false_negatives=10,
            precision=0.75,
            recall=0.60,
            f1_score=0.667,
            specificity=0.80,
            support=25
        )

        summary = metrics.get_summary()

        assert "Block2" in summary
        assert "TP=15" in summary
        assert "FP=5" in summary
        assert "0.7500" in summary  # Precision
        assert "0.6000" in summary  # Recall
        assert "Support: 25" in summary
