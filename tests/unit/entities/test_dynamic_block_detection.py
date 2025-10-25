"""
DynamicBlockDetection 단위 테스트
"""
import pytest
from datetime import date
from src.domain.entities import DynamicBlockDetection, BlockStatus


class TestDynamicBlockDetection:
    """DynamicBlockDetection 테스트"""

    def test_create_basic_detection(self):
        """기본 감지 객체 생성"""
        detection = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed"
        )

        assert detection.block_id == "block1"
        assert detection.block_type == 1
        assert detection.ticker == "025980"
        assert detection.condition_name == "seed"
        assert detection.status == BlockStatus.ACTIVE
        assert detection.id is None
        assert detection.pattern_id is None

    def test_create_with_pattern_id(self):
        """패턴 ID를 가진 감지 객체 생성"""
        detection = DynamicBlockDetection(
            block_id="block2",
            block_type=2,
            ticker="025980",
            condition_name="redetection",
            pattern_id=123
        )

        assert detection.pattern_id == 123

    def test_validation_missing_block_id(self):
        """block_id 없음 - 검증 실패"""
        with pytest.raises(ValueError, match="block_id"):
            DynamicBlockDetection(
                block_id="",
                block_type=1,
                ticker="025980",
                condition_name="seed"
            )

    def test_validation_invalid_block_type(self):
        """잘못된 block_type - 검증 실패"""
        with pytest.raises(ValueError, match="block_type"):
            DynamicBlockDetection(
                block_id="block1",
                block_type=0,  # 0은 허용되지 않음
                ticker="025980",
                condition_name="seed"
            )

    def test_validation_missing_ticker(self):
        """ticker 없음 - 검증 실패"""
        with pytest.raises(ValueError, match="ticker"):
            DynamicBlockDetection(
                block_id="block1",
                block_type=1,
                ticker="",
                condition_name="seed"
            )

    def test_validation_missing_condition_name(self):
        """condition_name 없음 - 검증 실패"""
        with pytest.raises(ValueError, match="condition_name"):
            DynamicBlockDetection(
                block_id="block1",
                block_type=1,
                ticker="025980",
                condition_name=""
            )

    def test_start_block(self):
        """블록 시작"""
        detection = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed"
        )

        start_date = date(2024, 1, 15)
        detection.start(start_date)

        assert detection.started_at == start_date
        assert detection.status == BlockStatus.ACTIVE
        assert detection.is_active()

    def test_start_already_started_block_fails(self):
        """이미 시작된 블록 다시 시작 - 실패"""
        detection = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed"
        )

        detection.start(date(2024, 1, 15))

        with pytest.raises(ValueError, match="이미 시작"):
            detection.start(date(2024, 1, 16))

    def test_update_peak(self):
        """최고가/최대거래량 갱신"""
        detection = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed"
        )

        detection.start(date(2024, 1, 15))

        # 첫 번째 갱신
        detection.update_peak(date(2024, 1, 15), 10000, 1000000)
        assert detection.peak_price == 10000
        assert detection.peak_volume == 1000000
        assert detection.peak_date == date(2024, 1, 15)

        # 더 높은 가격으로 갱신
        detection.update_peak(date(2024, 1, 16), 11000, 900000)
        assert detection.peak_price == 11000  # 갱신됨
        assert detection.peak_volume == 1000000  # 유지
        assert detection.peak_date == date(2024, 1, 16)  # 갱신됨

        # 더 많은 거래량으로 갱신
        detection.update_peak(date(2024, 1, 17), 10500, 1200000)
        assert detection.peak_price == 11000  # 유지
        assert detection.peak_volume == 1200000  # 갱신됨

    def test_complete_block(self):
        """블록 정상 완료"""
        detection = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed"
        )

        detection.start(date(2024, 1, 15))
        detection.complete(date(2024, 2, 10))

        assert detection.ended_at == date(2024, 2, 10)
        assert detection.status == BlockStatus.COMPLETED
        assert detection.is_completed()
        assert not detection.is_active()

    def test_complete_non_started_block_fails(self):
        """시작되지 않은 블록 완료 - 실패"""
        detection = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed"
        )

        # 아직 시작하지 않은 블록
        with pytest.raises(ValueError, match="아직 시작되지 않았습니다"):
            detection.complete(date(2024, 2, 10))

    def test_complete_already_completed_block_fails(self):
        """이미 완료된 블록 재완료 - 실패"""
        detection = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed"
        )

        detection.start(date(2024, 1, 15))
        detection.complete(date(2024, 2, 10))

        # 이미 완료된 블록을 다시 완료 시도
        with pytest.raises(ValueError, match="진행 중인 블록"):
            detection.complete(date(2024, 2, 15))

    def test_fail_block(self):
        """블록 실패"""
        detection = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed"
        )

        detection.start(date(2024, 1, 15))
        detection.fail(date(2024, 1, 20))

        assert detection.ended_at == date(2024, 1, 20)
        assert detection.status == BlockStatus.FAILED
        assert detection.is_failed()
        assert not detection.is_active()

    def test_add_parent_block(self):
        """부모 블록 추가"""
        detection = DynamicBlockDetection(
            block_id="block2",
            block_type=2,
            ticker="025980",
            condition_name="seed"
        )

        detection.add_parent_block(101)
        assert detection.parent_blocks == [101]

        detection.add_parent_block(102)
        assert detection.parent_blocks == [101, 102]

        # 중복 추가는 무시
        detection.add_parent_block(101)
        assert detection.parent_blocks == [101, 102]

    def test_metadata_operations(self):
        """메타데이터 설정/조회"""
        detection = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed"
        )

        detection.set_metadata("entry_surge_rate", 8.0)
        detection.set_metadata("exit_reason", "ma_breakdown")

        assert detection.get_metadata("entry_surge_rate") == 8.0
        assert detection.get_metadata("exit_reason") == "ma_breakdown"
        assert detection.get_metadata("unknown_key", "default") == "default"

    def test_to_dict(self):
        """딕셔너리 변환"""
        detection = DynamicBlockDetection(
            id=1,
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            pattern_id=123,
            started_at=date(2024, 1, 15),
            ended_at=date(2024, 2, 10),
            status=BlockStatus.COMPLETED,
            peak_price=11000.0,
            peak_volume=1500000,
            peak_date=date(2024, 1, 20),
            parent_blocks=[],
            metadata={"test": "value"}
        )

        data = detection.to_dict()

        assert data['id'] == 1
        assert data['block_id'] == "block1"
        assert data['block_type'] == 1
        assert data['ticker'] == "025980"
        assert data['condition_name'] == "seed"
        assert data['pattern_id'] == 123
        assert data['started_at'] == date(2024, 1, 15)
        assert data['ended_at'] == date(2024, 2, 10)
        assert data['status'] == "completed"
        assert data['peak_price'] == 11000.0
        assert data['peak_volume'] == 1500000
        assert data['peak_date'] == date(2024, 1, 20)
        assert data['metadata'] == {"test": "value"}

    def test_from_dict(self):
        """딕셔너리에서 생성"""
        data = {
            'id': 1,
            'block_id': "block2",
            'block_type': 2,
            'ticker': "005930",
            'condition_name': "redetection",
            'pattern_id': 456,
            'started_at': date(2024, 3, 1),
            'ended_at': date(2024, 3, 15),
            'status': "completed",
            'peak_price': 75000.0,
            'peak_volume': 2000000,
            'peak_date': date(2024, 3, 5),
            'parent_blocks': [100],
            'metadata': {"note": "test"}
        }

        detection = DynamicBlockDetection.from_dict(data)

        assert detection.id == 1
        assert detection.block_id == "block2"
        assert detection.block_type == 2
        assert detection.ticker == "005930"
        assert detection.condition_name == "redetection"
        assert detection.pattern_id == 456
        assert detection.started_at == date(2024, 3, 1)
        assert detection.ended_at == date(2024, 3, 15)
        assert detection.status == BlockStatus.COMPLETED
        assert detection.peak_price == 75000.0
        assert detection.peak_volume == 2000000
        assert detection.peak_date == date(2024, 3, 5)
        assert detection.parent_blocks == [100]
        assert detection.metadata == {"note": "test"}

    def test_multi_parent_blocks(self):
        """다중 부모 블록 지원"""
        detection = DynamicBlockDetection(
            block_id="block3",
            block_type=3,
            ticker="025980",
            condition_name="seed"
        )

        # Block2A와 Block2B 둘 다 부모로 설정 (병합 패턴)
        detection.add_parent_block(201)  # block2a
        detection.add_parent_block(202)  # block2b

        assert len(detection.parent_blocks) == 2
        assert 201 in detection.parent_blocks
        assert 202 in detection.parent_blocks

    def test_different_block_types(self):
        """다양한 블록 타입 지원"""
        # Block1
        b1 = DynamicBlockDetection("block1", 1, "025980", "seed")
        assert b1.block_type == 1

        # Block5
        b5 = DynamicBlockDetection("block5", 5, "025980", "seed")
        assert b5.block_type == 5

        # Block10 (확장 가능)
        b10 = DynamicBlockDetection("block10", 10, "025980", "seed")
        assert b10.block_type == 10


# ============================================================================
# Redetection Tests (NEW - 2025-10-25)
# ============================================================================

class TestDynamicBlockDetectionRedetection:
    """DynamicBlockDetection 재탐지 메서드 테스트"""

    def test_add_redetection(self):
        """재탐지 추가"""
        from src.domain.entities.detections import RedetectionEvent

        detection = DynamicBlockDetection(
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
            peak_volume=1000000
        )

        detection.add_redetection(redet)
        assert detection.get_redetection_count() == 1
        assert detection.redetections[0] == redet

    def test_get_active_redetection(self):
        """활성 재탐지 조회"""
        from src.domain.entities.detections import RedetectionEvent

        detection = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED
        )

        # 활성 재탐지 없음
        assert detection.get_active_redetection() is None

        # 활성 재탐지 추가
        redet1 = RedetectionEvent(
            sequence=1,
            parent_block_id="block1",
            started_at=date(2024, 1, 20),
            peak_price=10000.0,
            peak_volume=1000000,
            status=BlockStatus.ACTIVE
        )
        detection.add_redetection(redet1)

        assert detection.get_active_redetection() == redet1

        # 완료된 재탐지 추가 (활성 아님)
        redet2 = RedetectionEvent(
            sequence=2,
            parent_block_id="block1",
            started_at=date(2024, 2, 1),
            ended_at=date(2024, 2, 10),
            peak_price=10500.0,
            peak_volume=1100000,
            status=BlockStatus.COMPLETED
        )
        detection.add_redetection(redet2)

        # 여전히 redet1이 활성
        assert detection.get_active_redetection() == redet1

    def test_only_one_active_redetection(self):
        """한 번에 1개의 활성 재탐지만 가능"""
        from src.domain.entities.detections import RedetectionEvent

        detection = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED
        )

        redet1 = RedetectionEvent(
            sequence=1,
            parent_block_id="block1",
            started_at=date(2024, 1, 20),
            peak_price=10000.0,
            peak_volume=1000000,
            status=BlockStatus.ACTIVE
        )
        detection.add_redetection(redet1)

        # 첫 번째 재탐지가 활성인 상태에서 두 번째 활성 재탐지 시도
        redet2 = RedetectionEvent(
            sequence=2,
            parent_block_id="block1",
            started_at=date(2024, 1, 25),
            peak_price=10200.0,
            peak_volume=1050000,
            status=BlockStatus.ACTIVE
        )

        # 추가는 가능하지만 can_start_redetection은 False
        detection.add_redetection(redet2)
        assert not detection.can_start_redetection()

    def test_can_start_redetection(self):
        """재탐지 시작 가능 여부"""
        from src.domain.entities.detections import RedetectionEvent

        detection = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1)
        )

        # 완료되지 않은 블록 - 재탐지 불가
        assert not detection.can_start_redetection()

        # 완료
        detection.complete(date(2024, 1, 10))
        assert detection.can_start_redetection()

        # 활성 재탐지 추가
        redet = RedetectionEvent(
            sequence=1,
            parent_block_id="block1",
            started_at=date(2024, 1, 20),
            peak_price=10000.0,
            peak_volume=1000000,
            status=BlockStatus.ACTIVE
        )
        detection.add_redetection(redet)

        # 활성 재탐지 있음 - 새 재탐지 불가
        assert not detection.can_start_redetection()

        # 재탐지 완료
        redet.complete(date(2024, 1, 30))

        # 다시 재탐지 가능
        assert detection.can_start_redetection()

    def test_get_redetection_count(self):
        """총 재탐지 개수 조회"""
        from src.domain.entities.detections import RedetectionEvent

        detection = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED
        )

        assert detection.get_redetection_count() == 0

        # 재탐지 3개 추가
        redet_dates = [date(2024, 1, 20), date(2024, 2, 1), date(2024, 2, 15)]
        for i in range(3):
            redet = RedetectionEvent(
                sequence=i+1,
                parent_block_id="block1",
                started_at=redet_dates[i],
                peak_price=10000.0 + i*500,
                peak_volume=1000000 + i*100000,
                status=BlockStatus.COMPLETED if i < 2 else BlockStatus.ACTIVE
            )
            detection.add_redetection(redet)

        assert detection.get_redetection_count() == 3

    def test_get_completed_redetection_count(self):
        """완료된 재탐지 개수 조회"""
        from src.domain.entities.detections import RedetectionEvent

        detection = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED
        )

        assert detection.get_completed_redetection_count() == 0

        # 완료된 재탐지 2개
        completed_dates = [
            (date(2024, 1, 20), date(2024, 1, 25)),
            (date(2024, 2, 1), date(2024, 2, 10))
        ]
        for i in range(2):
            redet = RedetectionEvent(
                sequence=i+1,
                parent_block_id="block1",
                started_at=completed_dates[i][0],
                ended_at=completed_dates[i][1],
                peak_price=10000.0 + i*500,
                peak_volume=1000000 + i*100000,
                status=BlockStatus.COMPLETED
            )
            detection.add_redetection(redet)

        # 활성 재탐지 1개
        redet_active = RedetectionEvent(
            sequence=3,
            parent_block_id="block1",
            started_at=date(2024, 2, 1),
            peak_price=11000.0,
            peak_volume=1200000,
            status=BlockStatus.ACTIVE
        )
        detection.add_redetection(redet_active)

        assert detection.get_redetection_count() == 3
        assert detection.get_completed_redetection_count() == 2

    def test_redetections_empty_by_default(self):
        """기본적으로 재탐지 리스트는 빈 리스트"""
        detection = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed"
        )

        assert detection.redetections == []
        assert detection.get_redetection_count() == 0
