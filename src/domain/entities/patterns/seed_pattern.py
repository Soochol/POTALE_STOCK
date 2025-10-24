"""
Seed Pattern Entity

고품질 seed detection 결과를 저장하는 엔티티
Redetection 시 참조할 패턴 정보 포함
"""
from dataclasses import dataclass, field
from datetime import date
from typing import Optional, List, Dict, Any
from enum import Enum


class SeedPatternStatus(str, Enum):
    """Seed pattern 상태"""
    ACTIVE = "active"           # 활성화 (redetection 가능)
    ARCHIVED = "archived"       # 보관됨 (redetection 불가)
    DEPRECATED = "deprecated"   # 폐기됨


@dataclass
class BlockFeatures:
    """
    각 블록의 특징값

    Redetection 시 필터 기준으로 사용
    """
    block_id: str
    block_type: int
    started_at: date
    ended_at: Optional[date]
    duration_candles: int       # 캔들 개수

    # 가격 특징
    low_price: float
    high_price: float
    peak_price: float
    peak_date: date

    # 거래량 특징
    min_volume: int
    max_volume: int
    peak_volume: int
    avg_volume: int

    # 추가 메타데이터
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'block_id': self.block_id,
            'block_type': self.block_type,
            'started_at': self.started_at.isoformat(),
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'duration_candles': self.duration_candles,
            'low_price': self.low_price,
            'high_price': self.high_price,
            'peak_price': self.peak_price,
            'peak_date': self.peak_date.isoformat(),
            'min_volume': self.min_volume,
            'max_volume': self.max_volume,
            'peak_volume': self.peak_volume,
            'avg_volume': self.avg_volume,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BlockFeatures':
        """딕셔너리에서 생성"""
        return cls(
            block_id=data['block_id'],
            block_type=data['block_type'],
            started_at=date.fromisoformat(data['started_at']),
            ended_at=date.fromisoformat(data['ended_at']) if data.get('ended_at') else None,
            duration_candles=data['duration_candles'],
            low_price=data['low_price'],
            high_price=data['high_price'],
            peak_price=data['peak_price'],
            peak_date=date.fromisoformat(data['peak_date']),
            min_volume=data['min_volume'],
            max_volume=data['max_volume'],
            peak_volume=data['peak_volume'],
            avg_volume=data['avg_volume'],
            metadata=data.get('metadata', {})
        )


@dataclass
class SeedPattern:
    """
    Seed Pattern 엔티티

    고품질 seed detection 결과를 저장하고,
    redetection 시 참조할 패턴 정보를 관리
    """
    # 기본 정보
    pattern_name: str                          # 패턴 이름 (예: "seed_v1_025980")
    ticker: str                                # 종목 코드
    yaml_config_path: str                      # YAML 설정 파일 경로
    detection_date: date                       # 감지 날짜

    # Block features
    block_features: List[BlockFeatures]        # 각 블록의 특징값 리스트

    # Pattern shape (normalized sequences for matching)
    price_shape: List[float]                   # 정규화된 가격 시퀀스 [0~1]
    volume_shape: List[float]                  # 정규화된 볼륨 시퀀스 [0~1]

    # Optional fields
    id: Optional[int] = None                   # DB ID
    status: SeedPatternStatus = SeedPatternStatus.ACTIVE
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """검증"""
        if not self.pattern_name:
            raise ValueError("pattern_name is required")
        if not self.ticker:
            raise ValueError("ticker is required")
        if not self.yaml_config_path:
            raise ValueError("yaml_config_path is required")
        if not self.block_features:
            raise ValueError("block_features cannot be empty")
        if len(self.price_shape) != len(self.volume_shape):
            raise ValueError("price_shape and volume_shape must have same length")

    def get_block_feature(self, block_id: str) -> Optional[BlockFeatures]:
        """
        특정 블록의 특징값 조회

        Args:
            block_id: 블록 ID (예: "block1")

        Returns:
            BlockFeatures 또는 None
        """
        for feature in self.block_features:
            if feature.block_id == block_id:
                return feature
        return None

    def get_total_duration_candles(self) -> int:
        """
        전체 패턴의 duration (첫 블록 시작 ~ 마지막 블록 종료)

        Returns:
            총 캔들 개수
        """
        if not self.block_features:
            return 0

        # 시작일과 종료일 찾기
        start_date = min(f.started_at for f in self.block_features)

        # 종료일: 종료된 블록 중 최대값, 또는 마지막 블록의 시작일
        ended_features = [f for f in self.block_features if f.ended_at]
        if ended_features:
            end_date = max(f.ended_at for f in ended_features)
        else:
            end_date = max(f.started_at for f in self.block_features)

        # Duration 계산 (대략적, 실제로는 stock data로 계산해야 정확)
        return sum(f.duration_candles for f in self.block_features)

    def get_max_peak_price(self) -> float:
        """
        전체 패턴의 최고 가격

        Returns:
            최고 peak_price
        """
        if not self.block_features:
            return 0.0
        return max(f.peak_price for f in self.block_features)

    def get_max_peak_volume(self) -> int:
        """
        전체 패턴의 최대 거래량

        Returns:
            최대 peak_volume
        """
        if not self.block_features:
            return 0
        return max(f.peak_volume for f in self.block_features)

    def is_active(self) -> bool:
        """활성 상태 확인"""
        return self.status == SeedPatternStatus.ACTIVE

    def activate(self) -> None:
        """활성화"""
        self.status = SeedPatternStatus.ACTIVE

    def archive(self) -> None:
        """보관"""
        self.status = SeedPatternStatus.ARCHIVED

    def deprecate(self) -> None:
        """폐기"""
        self.status = SeedPatternStatus.DEPRECATED

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (JSON 직렬화용)"""
        return {
            'id': self.id,
            'pattern_name': self.pattern_name,
            'ticker': self.ticker,
            'yaml_config_path': self.yaml_config_path,
            'detection_date': self.detection_date.isoformat(),
            'block_features': [f.to_dict() for f in self.block_features],
            'price_shape': self.price_shape,
            'volume_shape': self.volume_shape,
            'status': self.status.value,
            'description': self.description,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SeedPattern':
        """딕셔너리에서 생성"""
        return cls(
            id=data.get('id'),
            pattern_name=data['pattern_name'],
            ticker=data['ticker'],
            yaml_config_path=data['yaml_config_path'],
            detection_date=date.fromisoformat(data['detection_date']),
            block_features=[BlockFeatures.from_dict(f) for f in data['block_features']],
            price_shape=data['price_shape'],
            volume_shape=data['volume_shape'],
            status=SeedPatternStatus(data.get('status', 'active')),
            description=data.get('description'),
            metadata=data.get('metadata', {})
        )

    @staticmethod
    def normalize_sequence(values: List[float]) -> List[float]:
        """
        시퀀스를 [0, 1] 범위로 정규화

        Args:
            values: 원본 값 리스트

        Returns:
            정규화된 값 리스트 [0~1]
        """
        if not values:
            return []

        min_val = min(values)
        max_val = max(values)

        if max_val == min_val:
            # 모든 값이 같으면 0.5로 반환
            return [0.5] * len(values)

        return [(v - min_val) / (max_val - min_val) for v in values]

    def __repr__(self) -> str:
        """문자열 표현"""
        return (
            f"SeedPattern(id={self.id}, "
            f"name='{self.pattern_name}', "
            f"ticker='{self.ticker}', "
            f"blocks={len(self.block_features)}, "
            f"status={self.status.value})"
        )
