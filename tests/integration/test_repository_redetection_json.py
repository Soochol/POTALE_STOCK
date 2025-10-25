"""
Repository Redetection JSON Serialization Tests

Repository의 재탐지 JSON 직렬화/역직렬화 통합 테스트
"""
import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.domain.entities.detections import DynamicBlockDetection, RedetectionEvent, BlockStatus
from src.infrastructure.repositories.dynamic_block_repository_impl import DynamicBlockRepositoryImpl
from src.infrastructure.database.models.base import Base


@pytest.fixture(scope="function")
def test_db_session():
    """테스트용 in-memory SQLite 세션"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()


@pytest.fixture
def repository(test_db_session):
    """DynamicBlockRepository 인스턴스"""
    return DynamicBlockRepositoryImpl(test_db_session)


class TestRedetectionJsonSerialization:
    """재탐지 JSON 직렬화 테스트"""

    def test_save_and_load_block_without_redetections(self, repository):
        """재탐지 없는 블록 저장 및 조회"""
        # 블록 생성 (재탐지 없음)
        block = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED,
            peak_price=10000.0,
            peak_volume=1000000
        )

        # 저장
        saved = repository.save(block)
        assert saved.id is not None

        # 조회
        loaded = repository.find_by_id(saved.id)
        assert loaded is not None
        assert loaded.block_id == "block1"
        assert loaded.get_redetection_count() == 0
        assert loaded.redetections == []

    def test_save_and_load_block_with_single_redetection(self, repository):
        """재탐지 1개 있는 블록 저장 및 조회"""
        # 블록 생성
        block = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED,
            peak_price=10000.0,
            peak_volume=1000000
        )

        # 재탐지 추가
        redetection = RedetectionEvent(
            sequence=1,
            parent_block_id="block1",
            started_at=date(2024, 1, 15),
            peak_price=9500.0,
            peak_volume=800000,
            status=BlockStatus.ACTIVE
        )
        block.add_redetection(redetection)

        # 저장
        saved = repository.save(block)
        assert saved.id is not None

        # 조회
        loaded = repository.find_by_id(saved.id)
        assert loaded is not None
        assert loaded.get_redetection_count() == 1

        # 재탐지 데이터 검증
        loaded_redet = loaded.redetections[0]
        assert loaded_redet.sequence == 1
        assert loaded_redet.parent_block_id == "block1"
        assert loaded_redet.started_at == date(2024, 1, 15)
        assert loaded_redet.peak_price == 9500.0
        assert loaded_redet.peak_volume == 800000
        assert loaded_redet.is_active()

    def test_save_and_load_block_with_multiple_redetections(self, repository):
        """여러 재탐지 있는 블록 저장 및 조회"""
        # 블록 생성
        block = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED,
            peak_price=10000.0,
            peak_volume=1000000
        )

        # 완료된 재탐지 2개
        redet1 = RedetectionEvent(
            sequence=1,
            parent_block_id="block1",
            started_at=date(2024, 1, 15),
            ended_at=date(2024, 1, 20),
            peak_price=9500.0,
            peak_volume=800000,
            status=BlockStatus.COMPLETED
        )
        block.add_redetection(redet1)

        redet2 = RedetectionEvent(
            sequence=2,
            parent_block_id="block1",
            started_at=date(2024, 2, 1),
            ended_at=date(2024, 2, 5),
            peak_price=9300.0,
            peak_volume=750000,
            status=BlockStatus.COMPLETED
        )
        block.add_redetection(redet2)

        # 활성 재탐지 1개
        redet3 = RedetectionEvent(
            sequence=3,
            parent_block_id="block1",
            started_at=date(2024, 2, 10),
            peak_price=9200.0,
            peak_volume=700000,
            status=BlockStatus.ACTIVE
        )
        block.add_redetection(redet3)

        # 저장
        saved = repository.save(block)

        # 조회
        loaded = repository.find_by_id(saved.id)
        assert loaded is not None
        assert loaded.get_redetection_count() == 3
        assert loaded.get_completed_redetection_count() == 2

        # 각 재탐지 검증
        assert loaded.redetections[0].sequence == 1
        assert loaded.redetections[0].is_completed()
        assert loaded.redetections[1].sequence == 2
        assert loaded.redetections[1].is_completed()
        assert loaded.redetections[2].sequence == 3
        assert loaded.redetections[2].is_active()

    def test_update_block_with_new_redetection(self, repository):
        """블록 업데이트 - 새 재탐지 추가"""
        # 초기 블록 저장 (재탐지 없음)
        block = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED,
            peak_price=10000.0,
            peak_volume=1000000
        )
        saved = repository.save(block)
        block_id = saved.id

        # 블록 다시 조회
        loaded = repository.find_by_id(block_id)
        assert loaded.get_redetection_count() == 0

        # 재탐지 추가
        redetection = RedetectionEvent(
            sequence=1,
            parent_block_id="block1",
            started_at=date(2024, 1, 15),
            peak_price=9500.0,
            peak_volume=800000,
            status=BlockStatus.ACTIVE
        )
        loaded.add_redetection(redetection)

        # 업데이트 저장
        repository.save(loaded)

        # 다시 조회하여 검증
        reloaded = repository.find_by_id(block_id)
        assert reloaded.get_redetection_count() == 1
        assert reloaded.redetections[0].sequence == 1

    def test_update_redetection_status(self, repository):
        """재탐지 상태 업데이트 (active → completed)"""
        # 활성 재탐지가 있는 블록 생성
        block = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED,
            peak_price=10000.0,
            peak_volume=1000000
        )

        redetection = RedetectionEvent(
            sequence=1,
            parent_block_id="block1",
            started_at=date(2024, 1, 15),
            peak_price=9500.0,
            peak_volume=800000,
            status=BlockStatus.ACTIVE
        )
        block.add_redetection(redetection)

        # 저장
        saved = repository.save(block)

        # 조회 및 재탐지 완료 처리
        loaded = repository.find_by_id(saved.id)
        active_redet = loaded.get_active_redetection()
        assert active_redet is not None
        active_redet.complete(date(2024, 1, 20))

        # 업데이트 저장
        repository.save(loaded)

        # 다시 조회하여 검증
        reloaded = repository.find_by_id(saved.id)
        assert reloaded.get_active_redetection() is None
        assert reloaded.get_completed_redetection_count() == 1
        assert reloaded.redetections[0].ended_at == date(2024, 1, 20)
        assert reloaded.redetections[0].is_completed()

    def test_redetection_peak_updates_persisted(self, repository):
        """재탐지 peak 업데이트가 올바르게 저장되는지"""
        # 블록 생성
        block = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED,
            peak_price=10000.0,
            peak_volume=1000000
        )

        redetection = RedetectionEvent(
            sequence=1,
            parent_block_id="block1",
            started_at=date(2024, 1, 15),
            peak_price=9500.0,
            peak_volume=800000,
            status=BlockStatus.ACTIVE
        )
        block.add_redetection(redetection)

        # 저장
        saved = repository.save(block)

        # 조회 및 peak 업데이트
        loaded = repository.find_by_id(saved.id)
        loaded.redetections[0].update_peak(9800.0, 900000)

        # 업데이트 저장
        repository.save(loaded)

        # 다시 조회하여 검증
        reloaded = repository.find_by_id(saved.id)
        assert reloaded.redetections[0].peak_price == 9800.0
        assert reloaded.redetections[0].peak_volume == 900000

    def test_find_by_ticker_includes_redetections(self, repository):
        """find_by_ticker 조회 시 재탐지 포함"""
        # 재탐지가 있는 블록 저장
        block = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED,
            peak_price=10000.0,
            peak_volume=1000000
        )

        redetection = RedetectionEvent(
            sequence=1,
            parent_block_id="block1",
            started_at=date(2024, 1, 15),
            peak_price=9500.0,
            peak_volume=800000,
            status=BlockStatus.ACTIVE
        )
        block.add_redetection(redetection)
        repository.save(block)

        # ticker로 조회
        blocks = repository.find_by_ticker("025980")
        assert len(blocks) == 1
        assert blocks[0].get_redetection_count() == 1
        assert blocks[0].redetections[0].sequence == 1

    def test_metadata_preserved_with_redetections(self, repository):
        """재탐지와 함께 custom metadata도 보존되는지"""
        # custom metadata가 있는 블록 생성
        block = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED,
            peak_price=10000.0,
            peak_volume=1000000,
            metadata={"custom_field": "custom_value", "score": 95.5}
        )

        # 재탐지 추가
        redetection = RedetectionEvent(
            sequence=1,
            parent_block_id="block1",
            started_at=date(2024, 1, 15),
            peak_price=9500.0,
            peak_volume=800000,
            status=BlockStatus.ACTIVE
        )
        block.add_redetection(redetection)

        # 저장
        saved = repository.save(block)

        # 조회
        loaded = repository.find_by_id(saved.id)

        # 재탐지와 metadata 모두 보존되었는지 확인
        assert loaded.get_redetection_count() == 1
        assert loaded.metadata["custom_field"] == "custom_value"
        assert loaded.metadata["score"] == 95.5
        # redetections는 metadata에서 분리되어 저장되므로 metadata에 없어야 함
        assert "redetections" not in loaded.metadata

    def test_empty_redetections_list_serialization(self, repository):
        """빈 redetections 리스트 직렬화"""
        # 명시적으로 빈 redetections 리스트가 있는 블록
        block = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED,
            peak_price=10000.0,
            peak_volume=1000000,
            redetections=[]
        )

        # 저장
        saved = repository.save(block)

        # 조회
        loaded = repository.find_by_id(saved.id)
        assert loaded.redetections == []
        assert loaded.get_redetection_count() == 0


class TestRedetectionJsonEdgeCases:
    """재탐지 JSON 직렬화 엣지 케이스 테스트"""

    def test_redetection_with_none_ended_at(self, repository):
        """ended_at이 None인 재탐지 직렬화"""
        block = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED,
            peak_price=10000.0,
            peak_volume=1000000
        )

        redetection = RedetectionEvent(
            sequence=1,
            parent_block_id="block1",
            started_at=date(2024, 1, 15),
            ended_at=None,  # 명시적으로 None
            peak_price=9500.0,
            peak_volume=800000,
            status=BlockStatus.ACTIVE
        )
        block.add_redetection(redetection)

        saved = repository.save(block)
        loaded = repository.find_by_id(saved.id)

        assert loaded.redetections[0].ended_at is None
        assert loaded.redetections[0].is_active()

    def test_very_large_redetection_count(self, repository):
        """많은 수의 재탐지 직렬화"""
        block = DynamicBlockDetection(
            block_id="block1",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED,
            peak_price=10000.0,
            peak_volume=1000000
        )

        # 20개의 완료된 재탐지 추가
        # 날짜 범위를 안전하게 설정 (1월~12월 분산)
        start_dates = [date(2024, 1 + (i // 2), 15) for i in range(20)]
        end_dates = [date(2024, 1 + (i // 2), 20) if i < 19 else None for i in range(20)]

        for i in range(20):
            redetection = RedetectionEvent(
                sequence=i+1,
                parent_block_id="block1",
                started_at=start_dates[i],
                ended_at=end_dates[i],  # 마지막은 None (활성)
                peak_price=10000.0 - (i * 100),
                peak_volume=1000000 - (i * 10000),
                status=BlockStatus.COMPLETED if i < 19 else BlockStatus.ACTIVE
            )
            block.add_redetection(redetection)

        saved = repository.save(block)
        loaded = repository.find_by_id(saved.id)

        assert loaded.get_redetection_count() == 20
        assert loaded.get_completed_redetection_count() == 19
        assert loaded.redetections[-1].is_active()

    def test_redetection_with_special_characters_in_block_id(self, repository):
        """block_id에 특수문자가 있는 경우"""
        block = DynamicBlockDetection(
            block_id="block_1_test",
            block_type=1,
            ticker="025980",
            condition_name="seed",
            started_at=date(2024, 1, 1),
            ended_at=date(2024, 1, 10),
            status=BlockStatus.COMPLETED,
            peak_price=10000.0,
            peak_volume=1000000
        )

        redetection = RedetectionEvent(
            sequence=1,
            parent_block_id="block_1_test",
            started_at=date(2024, 1, 15),
            peak_price=9500.0,
            peak_volume=800000,
            status=BlockStatus.ACTIVE
        )
        block.add_redetection(redetection)

        saved = repository.save(block)
        loaded = repository.find_by_id(saved.id)

        assert loaded.redetections[0].parent_block_id == "block_1_test"
