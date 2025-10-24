"""
Integration Tests for SeedPatternRepository

Seed pattern repository integration tests with in-memory DB
"""
import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.domain.entities.patterns import SeedPattern, SeedPatternStatus, BlockFeatures
from src.infrastructure.database.models.base import Base
from src.infrastructure.repositories.seed_pattern_repository_impl import SeedPatternRepositoryImpl


@pytest.fixture
def engine():
    """테스트용 인메모리 DB"""
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
    """SeedPatternRepository"""
    return SeedPatternRepositoryImpl(session)


@pytest.fixture
def sample_block_features():
    """샘플 블록 특징"""
    return [
        BlockFeatures(
            block_id='block1',
            block_type=1,
            started_at=date(2024, 1, 15),
            ended_at=date(2024, 2, 10),
            duration_candles=20,
            low_price=9500,
            high_price=12500,
            peak_price=12000,
            peak_date=date(2024, 1, 25),
            min_volume=500000,
            max_volume=2000000,
            peak_volume=1800000,
            avg_volume=1000000
        ),
        BlockFeatures(
            block_id='block2',
            block_type=2,
            started_at=date(2024, 2, 11),
            ended_at=date(2024, 3, 5),
            duration_candles=15,
            low_price=11000,
            high_price=13000,
            peak_price=12800,
            peak_date=date(2024, 2, 20),
            min_volume=600000,
            max_volume=1500000,
            peak_volume=1400000,
            avg_volume=900000
        )
    ]


@pytest.fixture
def sample_seed_pattern(sample_block_features):
    """샘플 seed pattern"""
    return SeedPattern(
        pattern_name='seed_v1_025980',
        ticker='025980',
        yaml_config_path='presets/examples/seed.yaml',
        detection_date=date(2024, 1, 15),
        block_features=sample_block_features,
        price_shape=[0.0, 0.3, 0.6, 0.8, 1.0, 0.9],
        volume_shape=[0.0, 0.5, 0.8, 1.0, 0.7, 0.5],
        description='Test seed pattern'
    )


class TestSeedPatternRepository:
    """SeedPatternRepository 통합 테스트"""

    def test_save_new_seed_pattern(self, repository, session, sample_seed_pattern):
        """새 seed pattern 저장"""
        # Save
        saved = repository.save(sample_seed_pattern)
        session.commit()

        # 검증
        assert saved.id is not None
        assert saved.pattern_name == 'seed_v1_025980'
        assert saved.ticker == '025980'
        assert len(saved.block_features) == 2

    def test_save_updates_existing_seed_pattern(self, repository, session, sample_seed_pattern):
        """기존 seed pattern 업데이트"""
        # 저장
        saved = repository.save(sample_seed_pattern)
        session.commit()
        original_id = saved.id

        # 수정
        saved.description = 'Updated description'
        saved.status = SeedPatternStatus.ARCHIVED

        # 재저장
        updated = repository.save(saved)
        session.commit()

        # 검증
        assert updated.id == original_id  # ID 동일
        assert updated.description == 'Updated description'
        assert updated.status == SeedPatternStatus.ARCHIVED

    def test_save_all(self, repository, session, sample_block_features):
        """여러 seed pattern 일괄 저장"""
        patterns = [
            SeedPattern(
                pattern_name=f'seed_v{i}_025980',
                ticker='025980',
                yaml_config_path='path/to/yaml',
                detection_date=date(2024, i, 1),
                block_features=sample_block_features,
                price_shape=[0.0, 1.0],
                volume_shape=[0.0, 1.0]
            )
            for i in range(1, 4)
        ]

        # 일괄 저장
        saved_patterns = repository.save_all(patterns)
        session.commit()

        # 검증
        assert len(saved_patterns) == 3
        assert all(p.id is not None for p in saved_patterns)

    def test_find_by_id(self, repository, session, sample_seed_pattern):
        """ID로 조회"""
        # 저장
        saved = repository.save(sample_seed_pattern)
        session.commit()

        # 조회
        found = repository.find_by_id(saved.id)

        # 검증
        assert found is not None
        assert found.id == saved.id
        assert found.pattern_name == saved.pattern_name
        assert len(found.block_features) == 2

    def test_find_by_id_not_found(self, repository):
        """ID로 조회 - 없는 경우"""
        found = repository.find_by_id(99999)
        assert found is None

    def test_find_by_name(self, repository, session, sample_seed_pattern):
        """이름으로 조회"""
        # 저장
        repository.save(sample_seed_pattern)
        session.commit()

        # 조회
        found = repository.find_by_name('seed_v1_025980')

        # 검증
        assert found is not None
        assert found.pattern_name == 'seed_v1_025980'

    def test_find_by_name_not_found(self, repository):
        """이름으로 조회 - 없는 경우"""
        found = repository.find_by_name('nonexistent')
        assert found is None

    def test_find_by_ticker(self, repository, session, sample_block_features):
        """종목으로 조회"""
        # 여러 패턴 저장
        for i in range(3):
            pattern = SeedPattern(
                pattern_name=f'seed_v{i}_025980',
                ticker='025980',
                yaml_config_path='path/to/yaml',
                detection_date=date(2024, 1, i + 1),
                block_features=sample_block_features,
                price_shape=[0.0, 1.0],
                volume_shape=[0.0, 1.0]
            )
            repository.save(pattern)
        session.commit()

        # 조회
        patterns = repository.find_by_ticker('025980')

        # 검증
        assert len(patterns) == 3
        assert all(p.ticker == '025980' for p in patterns)

    def test_find_by_ticker_with_status_filter(self, repository, session, sample_block_features):
        """종목으로 조회 - 상태 필터"""
        # ACTIVE 패턴 저장
        active_pattern = SeedPattern(
            pattern_name='seed_active',
            ticker='025980',
            yaml_config_path='path/to/yaml',
            detection_date=date(2024, 1, 1),
            block_features=sample_block_features,
            price_shape=[0.0, 1.0],
            volume_shape=[0.0, 1.0],
            status=SeedPatternStatus.ACTIVE
        )
        repository.save(active_pattern)

        # ARCHIVED 패턴 저장
        archived_pattern = SeedPattern(
            pattern_name='seed_archived',
            ticker='025980',
            yaml_config_path='path/to/yaml',
            detection_date=date(2024, 2, 1),
            block_features=sample_block_features,
            price_shape=[0.0, 1.0],
            volume_shape=[0.0, 1.0],
            status=SeedPatternStatus.ARCHIVED
        )
        repository.save(archived_pattern)
        session.commit()

        # ACTIVE만 조회
        active_patterns = repository.find_by_ticker('025980', status=SeedPatternStatus.ACTIVE)
        assert len(active_patterns) == 1
        assert active_patterns[0].status == SeedPatternStatus.ACTIVE

        # ARCHIVED만 조회
        archived_patterns = repository.find_by_ticker('025980', status=SeedPatternStatus.ARCHIVED)
        assert len(archived_patterns) == 1
        assert archived_patterns[0].status == SeedPatternStatus.ARCHIVED

    def test_find_active_patterns(self, repository, session, sample_block_features):
        """활성 패턴 조회"""
        # ACTIVE 패턴
        active = SeedPattern(
            pattern_name='seed_active',
            ticker='025980',
            yaml_config_path='path/to/yaml',
            detection_date=date(2024, 1, 1),
            block_features=sample_block_features,
            price_shape=[0.0, 1.0],
            volume_shape=[0.0, 1.0],
            status=SeedPatternStatus.ACTIVE
        )
        repository.save(active)

        # ARCHIVED 패턴
        archived = SeedPattern(
            pattern_name='seed_archived',
            ticker='025980',
            yaml_config_path='path/to/yaml',
            detection_date=date(2024, 2, 1),
            block_features=sample_block_features,
            price_shape=[0.0, 1.0],
            volume_shape=[0.0, 1.0],
            status=SeedPatternStatus.ARCHIVED
        )
        repository.save(archived)
        session.commit()

        # 활성 패턴만 조회
        active_patterns = repository.find_active_patterns()
        assert len(active_patterns) == 1
        assert active_patterns[0].status == SeedPatternStatus.ACTIVE

    def test_find_by_date_range(self, repository, session, sample_block_features):
        """날짜 범위로 조회"""
        # 여러 날짜의 패턴 저장
        dates = [date(2024, 1, 15), date(2024, 2, 20), date(2024, 3, 25)]
        for i, d in enumerate(dates):
            pattern = SeedPattern(
                pattern_name=f'seed_{i}',
                ticker='025980',
                yaml_config_path='path/to/yaml',
                detection_date=d,
                block_features=sample_block_features,
                price_shape=[0.0, 1.0],
                volume_shape=[0.0, 1.0]
            )
            repository.save(pattern)
        session.commit()

        # 2월 1일 ~ 3월 31일 조회
        patterns = repository.find_by_date_range(
            start_date=date(2024, 2, 1),
            end_date=date(2024, 3, 31)
        )

        # 검증 (2월, 3월 패턴만)
        assert len(patterns) == 2

    def test_find_all(self, repository, session, sample_block_features):
        """전체 조회"""
        # 3개 패턴 저장
        for i in range(3):
            pattern = SeedPattern(
                pattern_name=f'seed_{i}',
                ticker='025980',
                yaml_config_path='path/to/yaml',
                detection_date=date(2024, 1, i + 1),
                block_features=sample_block_features,
                price_shape=[0.0, 1.0],
                volume_shape=[0.0, 1.0]
            )
            repository.save(pattern)
        session.commit()

        # 전체 조회
        all_patterns = repository.find_all()
        assert len(all_patterns) == 3

    def test_find_all_with_pagination(self, repository, session, sample_block_features):
        """전체 조회 - 페이지네이션"""
        # 5개 패턴 저장
        for i in range(5):
            pattern = SeedPattern(
                pattern_name=f'seed_{i}',
                ticker='025980',
                yaml_config_path='path/to/yaml',
                detection_date=date(2024, 1, i + 1),
                block_features=sample_block_features,
                price_shape=[0.0, 1.0],
                volume_shape=[0.0, 1.0]
            )
            repository.save(pattern)
        session.commit()

        # 페이지네이션: limit=2, offset=1
        patterns = repository.find_all(limit=2, offset=1)
        assert len(patterns) == 2

    def test_count(self, repository, session, sample_block_features):
        """개수 조회"""
        # 3개 패턴 저장
        for i in range(3):
            pattern = SeedPattern(
                pattern_name=f'seed_{i}',
                ticker='025980',
                yaml_config_path='path/to/yaml',
                detection_date=date(2024, 1, i + 1),
                block_features=sample_block_features,
                price_shape=[0.0, 1.0],
                volume_shape=[0.0, 1.0]
            )
            repository.save(pattern)
        session.commit()

        # 전체 개수
        count = repository.count()
        assert count == 3

        # 특정 종목 개수
        count_ticker = repository.count(ticker='025980')
        assert count_ticker == 3

    def test_delete_by_id(self, repository, session, sample_seed_pattern):
        """ID로 삭제"""
        # 저장
        saved = repository.save(sample_seed_pattern)
        session.commit()

        # 삭제
        result = repository.delete_by_id(saved.id)
        session.commit()

        # 검증
        assert result is True
        assert repository.find_by_id(saved.id) is None

    def test_delete_by_id_not_found(self, repository):
        """ID로 삭제 - 없는 경우"""
        result = repository.delete_by_id(99999)
        assert result is False

    def test_delete_by_ticker(self, repository, session, sample_block_features):
        """종목으로 삭제"""
        # 3개 패턴 저장
        for i in range(3):
            pattern = SeedPattern(
                pattern_name=f'seed_{i}',
                ticker='025980',
                yaml_config_path='path/to/yaml',
                detection_date=date(2024, 1, i + 1),
                block_features=sample_block_features,
                price_shape=[0.0, 1.0],
                volume_shape=[0.0, 1.0]
            )
            repository.save(pattern)
        session.commit()

        # 종목으로 삭제
        deleted_count = repository.delete_by_ticker('025980')
        session.commit()

        # 검증
        assert deleted_count == 3
        assert repository.count(ticker='025980') == 0

    def test_update_status(self, repository, session, sample_seed_pattern):
        """상태 업데이트"""
        # 저장
        saved = repository.save(sample_seed_pattern)
        session.commit()
        assert saved.status == SeedPatternStatus.ACTIVE

        # 상태 변경
        result = repository.update_status(saved.id, SeedPatternStatus.ARCHIVED)
        session.commit()

        # 검증
        assert result is True
        updated = repository.find_by_id(saved.id)
        assert updated.status == SeedPatternStatus.ARCHIVED

    def test_update_status_not_found(self, repository):
        """상태 업데이트 - 없는 경우"""
        result = repository.update_status(99999, SeedPatternStatus.ARCHIVED)
        assert result is False
