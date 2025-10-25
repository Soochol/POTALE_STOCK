"""
Built-in Functions Redetection Tests

재탐지 관련 built-in 함수 테스트
"""
import pytest
from datetime import date
from src.domain.entities.conditions import function_registry
from src.domain.entities.detections import DynamicBlockDetection, BlockStatus, RedetectionEvent


class TestRedetectionBuiltinFunctions:
    """재탐지 관련 Built-in 함수 테스트"""

    def test_has_active_redetection_true(self):
        """has_active_redetection - 활성 재탐지 있음"""
        # Setup block with active redetection
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED
        )

        redet = RedetectionEvent(
            sequence=1,
            parent_block_id="block1",
            started_at=date(2024, 1, 20),
            peak_price=10000.0,
            peak_volume=1000000,
            status=BlockStatus.ACTIVE
        )
        block1.add_redetection(redet)

        context = {'block1': block1}

        # Get function
        func = function_registry.get('has_active_redetection')

        # Execute
        result = func('block1', context)

        assert result is True

    def test_has_active_redetection_false_no_redetections(self):
        """has_active_redetection - 재탐지 없음"""
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED
        )

        context = {'block1': block1}
        func = function_registry.get('has_active_redetection')

        result = func('block1', context)

        assert result is False

    def test_has_active_redetection_false_only_completed(self):
        """has_active_redetection - 완료된 재탐지만 있음"""
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED
        )

        redet = RedetectionEvent(
            sequence=1,
            parent_block_id="block1",
            started_at=date(2024, 1, 20),
            ended_at=date(2024, 1, 30),
            peak_price=10000.0,
            peak_volume=1000000,
            status=BlockStatus.COMPLETED
        )
        block1.add_redetection(redet)

        context = {'block1': block1}
        func = function_registry.get('has_active_redetection')

        result = func('block1', context)

        assert result is False

    def test_has_active_redetection_block_not_found(self):
        """has_active_redetection - 블록이 context에 없음"""
        context = {}
        func = function_registry.get('has_active_redetection')

        result = func('block1', context)

        assert result is False

    def test_redetection_count_zero(self):
        """redetection_count - 재탐지 개수 0"""
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed"
        )

        context = {'block1': block1}
        func = function_registry.get('redetection_count')

        result = func('block1', context)

        assert result == 0

    def test_redetection_count_multiple(self):
        """redetection_count - 여러 재탐지"""
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED
        )

        # 재탐지 3개 추가 (2개 완료, 1개 활성)
        for i in range(3):
            redet = RedetectionEvent(
                sequence=i+1,
                parent_block_id="block1",
                started_at=date(2024, 1, 20 + i*5),
                peak_price=10000.0,
                peak_volume=1000000,
                status=BlockStatus.COMPLETED if i < 2 else BlockStatus.ACTIVE
            )
            block1.add_redetection(redet)

        context = {'block1': block1}
        func = function_registry.get('redetection_count')

        result = func('block1', context)

        assert result == 3

    def test_redetection_count_block_not_found(self):
        """redetection_count - 블록이 context에 없음"""
        context = {}
        func = function_registry.get('redetection_count')

        result = func('block1', context)

        assert result == 0

    def test_completed_redetection_count_zero(self):
        """completed_redetection_count - 완료된 재탐지 개수 0"""
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed"
        )

        context = {'block1': block1}
        func = function_registry.get('completed_redetection_count')

        result = func('block1', context)

        assert result == 0

    def test_completed_redetection_count_mixed(self):
        """completed_redetection_count - 완료+활성 혼합"""
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED
        )

        # 완료된 재탐지 2개
        start_dates = [date(2024, 1, 20), date(2024, 2, 1)]
        end_dates = [date(2024, 1, 25), date(2024, 2, 5)]
        for i in range(2):
            redet = RedetectionEvent(
                sequence=i+1,
                parent_block_id="block1",
                started_at=start_dates[i],
                ended_at=end_dates[i],
                peak_price=10000.0,
                peak_volume=1000000,
                status=BlockStatus.COMPLETED
            )
            block1.add_redetection(redet)

        # 활성 재탐지 1개
        redet_active = RedetectionEvent(
            sequence=3,
            parent_block_id="block1",
            started_at=date(2024, 2, 10),
            peak_price=10000.0,
            peak_volume=1000000,
            status=BlockStatus.ACTIVE
        )
        block1.add_redetection(redet_active)

        context = {'block1': block1}
        func = function_registry.get('completed_redetection_count')

        result = func('block1', context)

        # 완료된 것만 2개
        assert result == 2

    def test_completed_redetection_count_all_completed(self):
        """completed_redetection_count - 모두 완료"""
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED
        )

        # 완료된 재탐지만 3개
        start_dates = [date(2024, 1, 20), date(2024, 1, 25), date(2024, 2, 1)]
        end_dates = [date(2024, 1, 25), date(2024, 1, 30), date(2024, 2, 5)]
        for i in range(3):
            redet = RedetectionEvent(
                sequence=i+1,
                parent_block_id="block1",
                started_at=start_dates[i],
                ended_at=end_dates[i],
                peak_price=10000.0,
                peak_volume=1000000,
                status=BlockStatus.COMPLETED
            )
            block1.add_redetection(redet)

        context = {'block1': block1}
        func = function_registry.get('completed_redetection_count')

        result = func('block1', context)

        assert result == 3

    def test_completed_redetection_count_block_not_found(self):
        """completed_redetection_count - 블록이 context에 없음"""
        context = {}
        func = function_registry.get('completed_redetection_count')

        result = func('block1', context)

        assert result == 0

    def test_redetection_functions_with_different_blocks(self):
        """여러 블록의 재탐지 독립성 확인"""
        # Block1 - 재탐지 2개
        block1 = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED
        )
        for i in range(2):
            redet = RedetectionEvent(
                sequence=i+1,
                parent_block_id="block1",
                started_at=date(2024, 1, 20 + i*5),
                peak_price=10000.0,
                peak_volume=1000000,
                status=BlockStatus.COMPLETED
            )
            block1.add_redetection(redet)

        # Block2 - 재탐지 3개
        block2 = DynamicBlockDetection(
            block_id="block2",
            block_type=2,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 2, 1),
            ended_at=date(2024, 2, 10),
            status=BlockStatus.COMPLETED
        )
        block2_start_dates = [date(2024, 2, 20), date(2024, 2, 25), date(2024, 3, 1)]
        for i in range(3):
            redet = RedetectionEvent(
                sequence=i+1,
                parent_block_id="block2",
                started_at=block2_start_dates[i],
                peak_price=15000.0,
                peak_volume=2000000,
                status=BlockStatus.COMPLETED
            )
            block2.add_redetection(redet)

        context = {'block1': block1, 'block2': block2}

        # Block1 체크
        func_count = function_registry.get('redetection_count')
        assert func_count('block1', context) == 2

        # Block2 체크
        assert func_count('block2', context) == 3
