"""
Unit Tests for SeedPattern Entity

Seed pattern 엔티티 테스트
"""
import pytest
from datetime import date

from src.domain.entities.patterns import SeedPattern, SeedPatternStatus, BlockFeatures


class TestBlockFeatures:
    """BlockFeatures 테스트"""

    def test_create_block_features(self):
        """BlockFeatures 생성"""
        features = BlockFeatures(
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
        )

        assert features.block_id == 'block1'
        assert features.block_type == 1
        assert features.duration_candles == 20
        assert features.peak_price == 12000
        assert features.peak_volume == 1800000

    def test_to_dict_and_from_dict(self):
        """딕셔너리 변환 테스트"""
        original = BlockFeatures(
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
            avg_volume=900000,
            metadata={'test': 'data'}
        )

        # to_dict → from_dict
        data = original.to_dict()
        restored = BlockFeatures.from_dict(data)

        # 비교
        assert restored.block_id == original.block_id
        assert restored.block_type == original.block_type
        assert restored.started_at == original.started_at
        assert restored.ended_at == original.ended_at
        assert restored.duration_candles == original.duration_candles
        assert restored.peak_price == original.peak_price
        assert restored.metadata == original.metadata


class TestSeedPattern:
    """SeedPattern 테스트"""

    @pytest.fixture
    def sample_block_features(self):
        """샘플 블록 특징 리스트"""
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

    def test_create_seed_pattern(self, sample_block_features):
        """SeedPattern 생성"""
        pattern = SeedPattern(
            pattern_name='seed_v1_025980',
            ticker='025980',
            yaml_config_path='presets/examples/seed_pattern.yaml',
            detection_date=date(2024, 1, 15),
            block_features=sample_block_features,
            price_shape=[0.0, 0.3, 0.6, 0.8, 1.0, 0.9],
            volume_shape=[0.0, 0.5, 0.8, 1.0, 0.7, 0.5]
        )

        assert pattern.pattern_name == 'seed_v1_025980'
        assert pattern.ticker == '025980'
        assert len(pattern.block_features) == 2
        assert len(pattern.price_shape) == 6
        assert pattern.status == SeedPatternStatus.ACTIVE

    def test_validation_empty_pattern_name(self, sample_block_features):
        """검증: pattern_name 필수"""
        with pytest.raises(ValueError, match="pattern_name is required"):
            SeedPattern(
                pattern_name='',
                ticker='025980',
                yaml_config_path='path/to/yaml',
                detection_date=date(2024, 1, 15),
                block_features=sample_block_features,
                price_shape=[0.0, 1.0],
                volume_shape=[0.0, 1.0]
            )

    def test_validation_empty_ticker(self, sample_block_features):
        """검증: ticker 필수"""
        with pytest.raises(ValueError, match="ticker is required"):
            SeedPattern(
                pattern_name='seed_v1',
                ticker='',
                yaml_config_path='path/to/yaml',
                detection_date=date(2024, 1, 15),
                block_features=sample_block_features,
                price_shape=[0.0, 1.0],
                volume_shape=[0.0, 1.0]
            )

    def test_validation_empty_block_features(self):
        """검증: block_features 필수"""
        with pytest.raises(ValueError, match="block_features cannot be empty"):
            SeedPattern(
                pattern_name='seed_v1',
                ticker='025980',
                yaml_config_path='path/to/yaml',
                detection_date=date(2024, 1, 15),
                block_features=[],
                price_shape=[0.0, 1.0],
                volume_shape=[0.0, 1.0]
            )

    def test_validation_shape_length_mismatch(self, sample_block_features):
        """검증: price_shape와 volume_shape 길이 일치"""
        with pytest.raises(ValueError, match="price_shape and volume_shape must have same length"):
            SeedPattern(
                pattern_name='seed_v1',
                ticker='025980',
                yaml_config_path='path/to/yaml',
                detection_date=date(2024, 1, 15),
                block_features=sample_block_features,
                price_shape=[0.0, 0.5, 1.0],
                volume_shape=[0.0, 1.0]  # 길이 불일치
            )

    def test_get_block_feature(self, sample_block_features):
        """특정 블록 특징 조회"""
        pattern = SeedPattern(
            pattern_name='seed_v1',
            ticker='025980',
            yaml_config_path='path/to/yaml',
            detection_date=date(2024, 1, 15),
            block_features=sample_block_features,
            price_shape=[0.0, 1.0],
            volume_shape=[0.0, 1.0]
        )

        # Block1 조회
        block1 = pattern.get_block_feature('block1')
        assert block1 is not None
        assert block1.block_id == 'block1'
        assert block1.peak_price == 12000

        # Block2 조회
        block2 = pattern.get_block_feature('block2')
        assert block2 is not None
        assert block2.block_id == 'block2'

        # 존재하지 않는 블록
        block3 = pattern.get_block_feature('block3')
        assert block3 is None

    def test_get_total_duration_candles(self, sample_block_features):
        """전체 duration 계산"""
        pattern = SeedPattern(
            pattern_name='seed_v1',
            ticker='025980',
            yaml_config_path='path/to/yaml',
            detection_date=date(2024, 1, 15),
            block_features=sample_block_features,
            price_shape=[0.0, 1.0],
            volume_shape=[0.0, 1.0]
        )

        total_duration = pattern.get_total_duration_candles()
        assert total_duration == 20 + 15  # block1: 20, block2: 15

    def test_get_max_peak_price(self, sample_block_features):
        """최고 가격 조회"""
        pattern = SeedPattern(
            pattern_name='seed_v1',
            ticker='025980',
            yaml_config_path='path/to/yaml',
            detection_date=date(2024, 1, 15),
            block_features=sample_block_features,
            price_shape=[0.0, 1.0],
            volume_shape=[0.0, 1.0]
        )

        max_price = pattern.get_max_peak_price()
        assert max_price == 12800  # block2의 peak_price

    def test_get_max_peak_volume(self, sample_block_features):
        """최대 거래량 조회"""
        pattern = SeedPattern(
            pattern_name='seed_v1',
            ticker='025980',
            yaml_config_path='path/to/yaml',
            detection_date=date(2024, 1, 15),
            block_features=sample_block_features,
            price_shape=[0.0, 1.0],
            volume_shape=[0.0, 1.0]
        )

        max_volume = pattern.get_max_peak_volume()
        assert max_volume == 1800000  # block1의 peak_volume

    def test_status_operations(self, sample_block_features):
        """상태 변경 테스트"""
        pattern = SeedPattern(
            pattern_name='seed_v1',
            ticker='025980',
            yaml_config_path='path/to/yaml',
            detection_date=date(2024, 1, 15),
            block_features=sample_block_features,
            price_shape=[0.0, 1.0],
            volume_shape=[0.0, 1.0]
        )

        # 초기 상태: ACTIVE
        assert pattern.is_active()
        assert pattern.status == SeedPatternStatus.ACTIVE

        # ARCHIVED로 변경
        pattern.archive()
        assert not pattern.is_active()
        assert pattern.status == SeedPatternStatus.ARCHIVED

        # 다시 ACTIVE로 변경
        pattern.activate()
        assert pattern.is_active()

        # DEPRECATED로 변경
        pattern.deprecate()
        assert pattern.status == SeedPatternStatus.DEPRECATED

    def test_to_dict_and_from_dict(self, sample_block_features):
        """딕셔너리 변환 테스트"""
        original = SeedPattern(
            pattern_name='seed_v1_025980',
            ticker='025980',
            yaml_config_path='presets/examples/seed.yaml',
            detection_date=date(2024, 1, 15),
            block_features=sample_block_features,
            price_shape=[0.0, 0.5, 1.0],
            volume_shape=[0.0, 0.7, 1.0],
            status=SeedPatternStatus.ACTIVE,
            description='Test pattern',
            metadata={'key': 'value'}
        )

        # to_dict → from_dict
        data = original.to_dict()
        restored = SeedPattern.from_dict(data)

        # 비교
        assert restored.pattern_name == original.pattern_name
        assert restored.ticker == original.ticker
        assert restored.yaml_config_path == original.yaml_config_path
        assert restored.detection_date == original.detection_date
        assert len(restored.block_features) == len(original.block_features)
        assert restored.price_shape == original.price_shape
        assert restored.volume_shape == original.volume_shape
        assert restored.status == original.status
        assert restored.description == original.description
        assert restored.metadata == original.metadata

    def test_normalize_sequence(self):
        """시퀀스 정규화 테스트"""
        # 일반 시퀀스
        values = [100, 200, 300, 400, 500]
        normalized = SeedPattern.normalize_sequence(values)

        assert normalized[0] == 0.0  # min
        assert normalized[-1] == 1.0  # max
        assert all(0 <= v <= 1 for v in normalized)

        # 모든 값이 같은 경우
        same_values = [100, 100, 100]
        normalized_same = SeedPattern.normalize_sequence(same_values)
        assert all(v == 0.5 for v in normalized_same)

        # 빈 리스트
        empty = SeedPattern.normalize_sequence([])
        assert empty == []

    def test_repr(self, sample_block_features):
        """문자열 표현 테스트"""
        pattern = SeedPattern(
            id=123,
            pattern_name='seed_v1_025980',
            ticker='025980',
            yaml_config_path='path/to/yaml',
            detection_date=date(2024, 1, 15),
            block_features=sample_block_features,
            price_shape=[0.0, 1.0],
            volume_shape=[0.0, 1.0]
        )

        repr_str = repr(pattern)
        assert 'SeedPattern' in repr_str
        assert 'id=123' in repr_str
        assert "name='seed_v1_025980'" in repr_str
        assert "ticker='025980'" in repr_str
        assert 'blocks=2' in repr_str
