"""
DynamicBlockRepository Integration Tests
"""
import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.domain.entities.detections import DynamicBlockDetection, BlockStatus
from src.infrastructure.database.models.base import Base
from src.infrastructure.database.models.dynamic_block_detection_model import DynamicBlockDetectionModel
from src.infrastructure.repositories.dynamic_block_repository_impl import DynamicBlockRepositoryImpl


@pytest.fixture
def engine():
    """테스트용 인메모리 DB 엔진"""
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def session(engine):
    """테스트용 세션"""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def repository(session):
    """테스트용 Repository"""
    return DynamicBlockRepositoryImpl(session)


class TestDynamicBlockRepository:
    """DynamicBlockRepository 통합 테스트"""

    def test_save_new_detection(self, repository):
        """새 블록 저장"""
        detection = DynamicBlockDetection(
            block_id='block1',
            block_type=1,
            ticker='025980',
            condition_name='seed'
        )
        detection.start(date(2024, 1, 15))

        # 저장
        saved = repository.save(detection)

        # 검증
        assert saved.id is not None
        assert saved.block_id == 'block1'
        assert saved.ticker == '025980'
        assert saved.started_at == date(2024, 1, 15)

    def test_save_updates_existing_detection(self, repository):
        """기존 블록 업데이트"""
        # 생성
        detection = DynamicBlockDetection(
            block_id='block1',
            block_type=1,
            ticker='025980',
            condition_name='seed'
        )
        detection.start(date(2024, 1, 15))
        saved = repository.save(detection)

        detection_id = saved.id

        # 업데이트
        saved.complete(date(2024, 2, 10))
        updated = repository.save(saved)

        # 검증
        assert updated.id == detection_id  # ID 동일
        assert updated.ended_at == date(2024, 2, 10)
        assert updated.is_completed()

    def test_find_by_id(self, repository):
        """ID로 조회"""
        # 저장
        detection = DynamicBlockDetection(
            block_id='block1',
            block_type=1,
            ticker='025980',
            condition_name='seed'
        )
        detection.start(date(2024, 1, 15))
        saved = repository.save(detection)

        # 조회
        found = repository.find_by_id(saved.id)

        # 검증
        assert found is not None
        assert found.id == saved.id
        assert found.block_id == 'block1'

    def test_find_by_id_not_found(self, repository):
        """존재하지 않는 ID - None 반환"""
        found = repository.find_by_id(9999)
        assert found is None

    def test_find_by_ticker(self, repository):
        """종목으로 조회"""
        # 여러 블록 저장
        d1 = DynamicBlockDetection('block1', 1, '025980', 'seed')
        d1.start(date(2024, 1, 15))
        repository.save(d1)

        d2 = DynamicBlockDetection('block2', 2, '025980', 'seed')
        d2.start(date(2024, 2, 1))
        repository.save(d2)

        d3 = DynamicBlockDetection('block1', 1, '005930', 'seed')
        d3.start(date(2024, 1, 20))
        repository.save(d3)

        # 종목으로 조회
        detections = repository.find_by_ticker('025980')

        # 검증
        assert len(detections) == 2
        assert all(d.ticker == '025980' for d in detections)

    def test_find_by_ticker_with_condition_name(self, repository):
        """종목 + 조건 이름으로 조회"""
        # Seed 조건
        d1 = DynamicBlockDetection('block1', 1, '025980', 'seed')
        d1.start(date(2024, 1, 15))
        repository.save(d1)

        # Redetection 조건
        d2 = DynamicBlockDetection('block1', 1, '025980', 'redetection')
        d2.start(date(2024, 2, 1))
        repository.save(d2)

        # Seed만 조회
        seed_detections = repository.find_by_ticker('025980', condition_name='seed')
        assert len(seed_detections) == 1
        assert seed_detections[0].condition_name == 'seed'

    def test_find_by_ticker_with_block_type(self, repository):
        """종목 + 블록 타입으로 조회"""
        d1 = DynamicBlockDetection('block1', 1, '025980', 'seed')
        d1.start(date(2024, 1, 15))
        repository.save(d1)

        d2 = DynamicBlockDetection('block2', 2, '025980', 'seed')
        d2.start(date(2024, 2, 1))
        repository.save(d2)

        # Block type 1만 조회
        block1_detections = repository.find_by_ticker('025980', block_type=1)
        assert len(block1_detections) == 1
        assert block1_detections[0].block_type == 1

    def test_find_active_blocks(self, repository):
        """진행 중인 블록 조회"""
        # Active 블록
        d1 = DynamicBlockDetection('block1', 1, '025980', 'seed')
        d1.start(date(2024, 1, 15))
        repository.save(d1)

        # Completed 블록
        d2 = DynamicBlockDetection('block2', 2, '025980', 'seed')
        d2.start(date(2024, 2, 1))
        d2.complete(date(2024, 2, 15))
        repository.save(d2)

        # Active만 조회
        active_blocks = repository.find_active_blocks('025980')
        assert len(active_blocks) == 1
        assert active_blocks[0].is_active()

    def test_find_active_blocks_with_block_id(self, repository):
        """특정 block_id의 진행 중인 블록 조회"""
        d1 = DynamicBlockDetection('block1', 1, '025980', 'seed')
        d1.start(date(2024, 1, 15))
        repository.save(d1)

        d2 = DynamicBlockDetection('block2', 2, '025980', 'seed')
        d2.start(date(2024, 2, 1))
        repository.save(d2)

        # block1만 조회
        block1_active = repository.find_active_blocks('025980', block_id='block1')
        assert len(block1_active) == 1
        assert block1_active[0].block_id == 'block1'

    def test_find_by_pattern_id(self, repository):
        """패턴 ID로 조회"""
        d1 = DynamicBlockDetection('block1', 1, '025980', 'seed', pattern_id=100)
        d1.start(date(2024, 1, 15))
        repository.save(d1)

        d2 = DynamicBlockDetection('block2', 2, '025980', 'seed', pattern_id=100)
        d2.start(date(2024, 2, 1))
        repository.save(d2)

        d3 = DynamicBlockDetection('block1', 1, '025980', 'seed', pattern_id=200)
        d3.start(date(2024, 3, 1))
        repository.save(d3)

        # Pattern 100 조회
        pattern_blocks = repository.find_by_pattern_id(100)
        assert len(pattern_blocks) == 2
        assert all(d.pattern_id == 100 for d in pattern_blocks)

    def test_find_by_date_range(self, repository):
        """날짜 범위로 조회"""
        d1 = DynamicBlockDetection('block1', 1, '025980', 'seed')
        d1.start(date(2024, 1, 15))
        repository.save(d1)

        d2 = DynamicBlockDetection('block2', 2, '025980', 'seed')
        d2.start(date(2024, 2, 1))
        repository.save(d2)

        d3 = DynamicBlockDetection('block3', 3, '025980', 'seed')
        d3.start(date(2024, 3, 1))
        repository.save(d3)

        # 1월~2월 범위 조회
        detections = repository.find_by_date_range(
            '025980',
            date(2024, 1, 1),
            date(2024, 2, 28)
        )

        assert len(detections) == 2
        assert detections[0].started_at == date(2024, 1, 15)
        assert detections[1].started_at == date(2024, 2, 1)

    def test_delete_by_id(self, repository):
        """ID로 삭제"""
        d1 = DynamicBlockDetection('block1', 1, '025980', 'seed')
        d1.start(date(2024, 1, 15))
        saved = repository.save(d1)

        # 삭제
        result = repository.delete_by_id(saved.id)
        assert result is True

        # 조회 시 None
        found = repository.find_by_id(saved.id)
        assert found is None

    def test_delete_by_id_not_found(self, repository):
        """존재하지 않는 ID 삭제 - False 반환"""
        result = repository.delete_by_id(9999)
        assert result is False

    def test_delete_by_ticker(self, repository):
        """종목으로 삭제"""
        d1 = DynamicBlockDetection('block1', 1, '025980', 'seed')
        d1.start(date(2024, 1, 15))
        repository.save(d1)

        d2 = DynamicBlockDetection('block2', 2, '025980', 'seed')
        d2.start(date(2024, 2, 1))
        repository.save(d2)

        d3 = DynamicBlockDetection('block1', 1, '005930', 'seed')
        d3.start(date(2024, 1, 20))
        repository.save(d3)

        # 025980 삭제
        count = repository.delete_by_ticker('025980')
        assert count == 2

        # 005930은 남아있음
        remaining = repository.find_by_ticker('005930')
        assert len(remaining) == 1

    def test_delete_by_ticker_with_condition_name(self, repository):
        """종목 + 조건으로 삭제"""
        d1 = DynamicBlockDetection('block1', 1, '025980', 'seed')
        d1.start(date(2024, 1, 15))
        repository.save(d1)

        d2 = DynamicBlockDetection('block1', 1, '025980', 'redetection')
        d2.start(date(2024, 2, 1))
        repository.save(d2)

        # Seed만 삭제
        count = repository.delete_by_ticker('025980', condition_name='seed')
        assert count == 1

        # Redetection은 남아있음
        remaining = repository.find_by_ticker('025980')
        assert len(remaining) == 1
        assert remaining[0].condition_name == 'redetection'

    def test_save_all(self, repository):
        """일괄 저장"""
        detections = [
            DynamicBlockDetection('block1', 1, '025980', 'seed'),
            DynamicBlockDetection('block2', 2, '025980', 'seed'),
            DynamicBlockDetection('block3', 3, '025980', 'seed'),
        ]

        for d in detections:
            d.start(date(2024, 1, 15))

        # 일괄 저장
        saved_detections = repository.save_all(detections)

        # 검증
        assert len(saved_detections) == 3
        assert all(d.id is not None for d in saved_detections)

    def test_parent_blocks_persistence(self, repository):
        """부모 블록 리스트 저장/조회"""
        detection = DynamicBlockDetection('block3', 3, '025980', 'seed')
        detection.start(date(2024, 1, 15))
        detection.add_parent_block(100)
        detection.add_parent_block(200)

        saved = repository.save(detection)

        # 조회
        found = repository.find_by_id(saved.id)
        assert found.parent_blocks == [100, 200]

    def test_metadata_persistence(self, repository):
        """메타데이터 저장/조회"""
        detection = DynamicBlockDetection('block1', 1, '025980', 'seed')
        detection.start(date(2024, 1, 15))
        detection.set_metadata('entry_surge_rate', 8.0)
        detection.set_metadata('note', 'test')

        saved = repository.save(detection)

        # 조회
        found = repository.find_by_id(saved.id)
        assert found.get_metadata('entry_surge_rate') == 8.0
        assert found.get_metadata('note') == 'test'
