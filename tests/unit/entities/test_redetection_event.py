"""
RedetectionEvent Entity 단위 테스트

재탐지 이벤트 도메인 엔티티 테스트
"""
import pytest
from datetime import date
from src.domain.entities.detections import RedetectionEvent, BlockStatus


class TestRedetectionEvent:
    """RedetectionEvent 테스트"""

    def test_create_redetection_event(self):
        """재탐지 이벤트 생성"""
        redet = RedetectionEvent(
            sequence=1,
            parent_block_id="block1",
            started_at=date(2024, 1, 15),
            peak_price=10000.0,
            peak_volume=1000000
        )

        assert redet.sequence == 1
        assert redet.parent_block_id == "block1"
        assert redet.started_at == date(2024, 1, 15)
        assert redet.ended_at is None
        assert redet.peak_price == 10000.0
        assert redet.peak_volume == 1000000
        assert redet.status == BlockStatus.ACTIVE
        assert redet.is_active()

    def test_complete_redetection(self):
        """재탐지 완료"""
        redet = RedetectionEvent(
            sequence=1,
            parent_block_id="block1",
            started_at=date(2024, 1, 15),
            peak_price=10000.0,
            peak_volume=1000000
        )

        redet.complete(date(2024, 1, 20))

        assert redet.ended_at == date(2024, 1, 20)
        assert redet.status == BlockStatus.COMPLETED
        assert redet.is_completed()
        assert not redet.is_active()

    def test_complete_already_completed_redetection_fails(self):
        """이미 완료된 재탐지 재완료 - 실패"""
        redet = RedetectionEvent(
            sequence=1,
            parent_block_id="block1",
            started_at=date(2024, 1, 15),
            peak_price=10000.0,
            peak_volume=1000000
        )

        redet.complete(date(2024, 1, 20))

        # 이미 완료된 재탐지 재완료 시도
        with pytest.raises(ValueError, match="already completed"):
            redet.complete(date(2024, 1, 25))

    def test_update_peak_price(self):
        """Peak 가격 업데이트"""
        redet = RedetectionEvent(
            sequence=1,
            parent_block_id="block1",
            started_at=date(2024, 1, 15),
            peak_price=10000.0,
            peak_volume=1000000
        )

        # 더 높은 가격으로 업데이트
        redet.update_peak(11000.0, 900000)
        assert redet.peak_price == 11000.0
        assert redet.peak_volume == 1000000  # 유지

        # 더 낮은 가격 시도 (업데이트 안됨)
        redet.update_peak(10500.0, 800000)
        assert redet.peak_price == 11000.0  # 유지

    def test_update_peak_volume(self):
        """Peak 거래량 업데이트"""
        redet = RedetectionEvent(
            sequence=1,
            parent_block_id="block1",
            started_at=date(2024, 1, 15),
            peak_price=10000.0,
            peak_volume=1000000
        )

        # 더 많은 거래량으로 업데이트
        redet.update_peak(9500.0, 1200000)
        assert redet.peak_price == 10000.0  # 유지
        assert redet.peak_volume == 1200000  # 업데이트

    def test_to_dict_serialization(self):
        """딕셔너리 직렬화"""
        redet = RedetectionEvent(
            sequence=2,
            parent_block_id="block2",
            started_at=date(2024, 2, 1),
            ended_at=date(2024, 2, 10),
            peak_price=15000.0,
            peak_volume=2000000,
            status=BlockStatus.COMPLETED
        )

        data = redet.to_dict()

        assert data['sequence'] == 2
        assert data['parent_block_id'] == "block2"
        assert data['started_at'] == "2024-02-01"
        assert data['ended_at'] == "2024-02-10"
        assert data['peak_price'] == 15000.0
        assert data['peak_volume'] == 2000000
        assert data['status'] == "completed"

    def test_from_dict_deserialization(self):
        """딕셔너리에서 생성"""
        data = {
            'sequence': 3,
            'parent_block_id': "block3",
            'started_at': "2024-03-01",
            'ended_at': "2024-03-15",
            'peak_price': 20000.0,
            'peak_volume': 3000000,
            'status': "completed"
        }

        redet = RedetectionEvent.from_dict(data)

        assert redet.sequence == 3
        assert redet.parent_block_id == "block3"
        assert redet.started_at == date(2024, 3, 1)
        assert redet.ended_at == date(2024, 3, 15)
        assert redet.peak_price == 20000.0
        assert redet.peak_volume == 3000000
        assert redet.status == BlockStatus.COMPLETED

    def test_from_dict_with_none_ended_at(self):
        """ended_at이 None인 경우 역직렬화"""
        data = {
            'sequence': 1,
            'parent_block_id': "block1",
            'started_at': "2024-01-15",
            'ended_at': None,
            'peak_price': 10000.0,
            'peak_volume': 1000000,
            'status': "active"
        }

        redet = RedetectionEvent.from_dict(data)

        assert redet.ended_at is None
        assert redet.is_active()

    def test_multiple_redetections_sequence(self):
        """여러 재탐지 이벤트 순서 검증"""
        redet1 = RedetectionEvent(1, "block1", date(2024, 1, 1), peak_price=10000.0, peak_volume=1000000)
        redet2 = RedetectionEvent(2, "block1", date(2024, 2, 1), peak_price=10500.0, peak_volume=1100000)
        redet3 = RedetectionEvent(3, "block1", date(2024, 3, 1), peak_price=11000.0, peak_volume=1200000)

        # Sequence가 올바르게 설정되었는지 확인
        assert redet1.sequence == 1
        assert redet2.sequence == 2
        assert redet3.sequence == 3

        # 모두 같은 parent_block_id
        assert redet1.parent_block_id == redet2.parent_block_id == redet3.parent_block_id

    def test_different_parent_blocks_redetections(self):
        """다른 부모 블록의 재탐지"""
        redet_b1 = RedetectionEvent(1, "block1", date(2024, 1, 1), peak_price=10000.0, peak_volume=1000000)
        redet_b2 = RedetectionEvent(1, "block2", date(2024, 1, 1), peak_price=15000.0, peak_volume=2000000)

        # 다른 블록의 재탐지는 sequence가 독립적
        assert redet_b1.sequence == 1
        assert redet_b2.sequence == 1
        assert redet_b1.parent_block_id != redet_b2.parent_block_id
