"""
Condition Preset Models
Seed 및 재탐지 조건 프리셋 모델
"""
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, Index

from .base import Base


class SeedConditionPreset(Base):
    """Seed 조건 프리셋 테이블 (엄격한 조건)"""
    __tablename__ = 'seed_condition_preset'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, comment='프리셋 이름')
    description = Column(String(500), comment='프리셋 설명')

    # Block1 진입 조건
    block1_entry_surge_rate = Column(Float, nullable=True, comment='진입 급등률 (%) (None=조건 비활성화)')
    block1_entry_ma_period = Column(Integer, nullable=False, comment='진입 이동평균선 기간 (None이면 MA 조건 전체 skip)')
    block1_entry_max_deviation_ratio = Column(Float, nullable=True, comment='최대 이격도 비율 (None=조건 비활성화)')
    block1_entry_min_trading_value = Column(Float, nullable=True, comment='최소 거래대금 (억원) (None=조건 비활성화)')
    block1_entry_volume_high_days = Column(Integer, nullable=True, comment='N일 신고거래량 (달력 기준) (None=조건 비활성화)')
    block1_entry_volume_spike_ratio = Column(Float, nullable=True, comment='전날 대비 거래량 비율 (%) (None=조건 비활성화)')
    block1_entry_price_high_days = Column(Integer, nullable=True, comment='N일 신고가 (달력 기준) (None=조건 비활성화)')

    # 종료 조건
    block1_exit_condition_type = Column(String(50), nullable=False, comment='종료 조건 타입')
    block1_exit_ma_period = Column(Integer, comment='종료용 이동평균선 기간')
    block1_auto_exit_on_next_block = Column(Integer, default=0, nullable=False, comment='Block2 시작 시 Block1 자동 종료 (0=false, 1=true)')

    # 시스템
    block1_min_start_interval_days = Column(Integer, default=20, nullable=False, comment='같은 레벨 블록 중복 방지: 시작 후 N일간 새 블록 탐지 금지')

    # Block2 추가 조건
    block2_volume_ratio = Column(Float, comment='Block1 최고 거래량 대비 비율 (%)')
    block2_low_price_margin = Column(Float, comment='Block1 최고가 저가 마진 (%)')
    block2_min_candles_after_block1 = Column(Integer, comment='Block1 시작 후 최소 캔들 수')
    block2_max_candles_after_block1 = Column(Integer, nullable=True, comment='Block1 시작 후 최대 캔들 수')

    # Block3 추가 조건
    block3_volume_ratio = Column(Float, comment='Block2 최고 거래량 대비 비율 (%)')
    block3_low_price_margin = Column(Float, comment='Block2 최고가 저가 마진 (%)')
    block3_min_candles_after_block2 = Column(Integer, comment='Block2 시작 후 최소 캔들 수')
    block3_max_candles_after_block2 = Column(Integer, nullable=True, comment='Block2 시작 후 최대 캔들 수')

    # Block4 추가 조건
    block4_volume_ratio = Column(Float, comment='Block3 최고 거래량 대비 비율 (%)')
    block4_low_price_margin = Column(Float, comment='Block3 최고가 저가 마진 (%)')
    block4_min_candles_after_block3 = Column(Integer, comment='Block3 시작 후 최소 캔들 수')
    block4_max_candles_after_block3 = Column(Integer, nullable=True, comment='Block3 시작 후 최대 캔들 수')

    # Block2 전용 파라미터 (Optional)
    block2_entry_surge_rate = Column(Float, comment='Block2 전용 진입 급등률 (%)')
    block2_entry_ma_period = Column(Integer, comment='Block2 전용 진입 이동평균선 기간')
    block2_entry_max_deviation_ratio = Column(Float, comment='Block2 전용 최대 이격도')
    block2_entry_min_trading_value = Column(Float, comment='Block2 전용 최소 거래대금')
    block2_entry_volume_high_days = Column(Integer, comment='Block2 전용 N일 신고거래량 (달력 기준)')
    block2_entry_volume_spike_ratio = Column(Float, comment='Block2 전용 거래량 비율')
    block2_entry_price_high_days = Column(Integer, comment='Block2 전용 N일 신고가 (달력 기준)')
    block2_exit_condition_type = Column(String(50), comment='Block2 전용 종료 조건 타입')
    block2_exit_ma_period = Column(Integer, comment='Block2 전용 종료 이평선 기간')
    block2_auto_exit_on_next_block = Column(Integer, default=0, nullable=False, comment='Block3 시작 시 Block2 자동 종료 (0=false, 1=true)')
    block2_min_start_interval_days = Column(Integer, comment='Block2 전용: 같은 레벨 블록 중복 방지 (시작 후 N일간)')

    # Block3 전용 파라미터 (Optional)
    block3_entry_surge_rate = Column(Float, comment='Block3 전용 진입 급등률 (%)')
    block3_entry_ma_period = Column(Integer, comment='Block3 전용 진입 이동평균선 기간')
    block3_entry_max_deviation_ratio = Column(Float, comment='Block3 전용 최대 이격도')
    block3_entry_min_trading_value = Column(Float, comment='Block3 전용 최소 거래대금')
    block3_entry_volume_high_days = Column(Integer, comment='Block3 전용 N일 신고거래량 (달력 기준)')
    block3_entry_volume_spike_ratio = Column(Float, comment='Block3 전용 거래량 비율')
    block3_entry_price_high_days = Column(Integer, comment='Block3 전용 N일 신고가 (달력 기준)')
    block3_exit_condition_type = Column(String(50), comment='Block3 전용 종료 조건 타입')
    block3_exit_ma_period = Column(Integer, comment='Block3 전용 종료 이평선 기간')
    block3_auto_exit_on_next_block = Column(Integer, default=0, nullable=False, comment='Block4 시작 시 Block3 자동 종료 (0=false, 1=true)')
    block3_min_start_interval_days = Column(Integer, comment='Block3 전용: 같은 레벨 블록 중복 방지 (시작 후 N일간)')

    # Block4 전용 파라미터 (Optional)
    block4_entry_surge_rate = Column(Float, comment='Block4 전용 진입 급등률 (%)')
    block4_entry_ma_period = Column(Integer, comment='Block4 전용 진입 이동평균선 기간')
    block4_entry_max_deviation_ratio = Column(Float, comment='Block4 전용 최대 이격도')
    block4_entry_min_trading_value = Column(Float, comment='Block4 전용 최소 거래대금')
    block4_entry_volume_high_days = Column(Integer, comment='Block4 전용 N일 신고거래량 (달력 기준)')
    block4_entry_volume_spike_ratio = Column(Float, comment='Block4 전용 거래량 비율')
    block4_entry_price_high_days = Column(Integer, comment='Block4 전용 N일 신고가 (달력 기준)')
    block4_exit_condition_type = Column(String(50), comment='Block4 전용 종료 조건 타입')
    block4_exit_ma_period = Column(Integer, comment='Block4 전용 종료 이평선 기간')
    block4_auto_exit_on_next_block = Column(Integer, default=0, nullable=False, comment='일관성을 위해 포함 (Block5 없음, 실제 작동 안 함)')
    block4_min_start_interval_days = Column(Integer, comment='Block4 전용: 같은 레벨 블록 중복 방지 (시작 후 N일간)')

    # 메타데이터
    is_active = Column(Integer, default=1, comment='활성 여부')
    created_at = Column(DateTime, default=datetime.now, comment='생성일시')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='수정일시')

    # 인덱스
    __table_args__ = (
        Index('ix_seed_condition_name', 'name', unique=True),
        Index('ix_seed_condition_active', 'is_active'),
    )

    def __repr__(self):
        return f"<SeedConditionPreset(name={self.name}, surge_rate={self.block1_entry_surge_rate}%)>"


class RedetectionConditionPreset(Base):
    """재탐지 조건 프리셋 테이블 (완화된 조건 + 가격 범위)"""
    __tablename__ = 'redetection_condition_preset'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, comment='프리셋 이름')
    description = Column(String(500), comment='프리셋 설명')

    # Block1 진입 조건 (완화)
    block1_entry_surge_rate = Column(Float, nullable=True, comment='진입 급등률 (%) - 완화 (None=조건 비활성화)')
    block1_entry_ma_period = Column(Integer, nullable=False, comment='진입 이동평균선 기간 (None이면 MA 조건 전체 skip)')
    block1_entry_max_deviation_ratio = Column(Float, nullable=True, comment='최대 이격도 비율 (None=조건 비활성화)')
    block1_entry_min_trading_value = Column(Float, nullable=True, comment='최소 거래대금 (억원) (None=조건 비활성화)')
    block1_entry_volume_high_days = Column(Integer, nullable=True, comment='N일 신고거래량 (달력 기준) (None=조건 비활성화)')
    block1_entry_volume_spike_ratio = Column(Float, nullable=True, comment='전날 대비 거래량 비율 (%) - 완화 (None=조건 비활성화)')
    block1_entry_price_high_days = Column(Integer, nullable=True, comment='N일 신고가 (달력 기준) (None=조건 비활성화)')

    # 재탐지 전용: 가격 범위 Tolerance
    block1_tolerance_pct = Column(Float, nullable=False, default=10.0, comment='Block1 재탐지 가격 범위 (±%)')
    block2_tolerance_pct = Column(Float, nullable=False, default=15.0, comment='Block2 재탐지 가격 범위 (±%)')
    block3_tolerance_pct = Column(Float, nullable=False, default=20.0, comment='Block3 재탐지 가격 범위 (±%)')
    block4_tolerance_pct = Column(Float, nullable=False, default=25.0, comment='Block4 재탐지 가격 범위 (±%)')

    # 재탐지 전용: 기간 범위 (Seed 발생일 기준, 달력상 일수)
    block1_redetection_min_days_after_seed = Column(Integer, nullable=False, default=0, comment='Block1 Seed + 최소일수 (달력 기준)')
    block1_redetection_max_days_after_seed = Column(Integer, nullable=False, default=1825, comment='Block1 Seed + 최대일수 (달력 기준, 5년)')
    block2_redetection_min_days_after_seed = Column(Integer, nullable=False, default=0, comment='Block2 Seed + 최소일수 (달력 기준)')
    block2_redetection_max_days_after_seed = Column(Integer, nullable=False, default=1825, comment='Block2 Seed + 최대일수 (달력 기준, 5년)')
    block3_redetection_min_days_after_seed = Column(Integer, nullable=False, default=0, comment='Block3 Seed + 최소일수 (달력 기준)')
    block3_redetection_max_days_after_seed = Column(Integer, nullable=False, default=1825, comment='Block3 Seed + 최대일수 (달력 기준, 5년)')
    block4_redetection_min_days_after_seed = Column(Integer, nullable=False, default=0, comment='Block4 Seed + 최소일수 (달력 기준)')
    block4_redetection_max_days_after_seed = Column(Integer, nullable=False, default=1825, comment='Block4 Seed + 최대일수 (달력 기준, 5년)')

    # 종료 조건
    block1_exit_condition_type = Column(String(50), nullable=False, comment='종료 조건 타입')
    block1_exit_ma_period = Column(Integer, comment='종료용 이동평균선 기간')
    block1_auto_exit_on_next_block = Column(Integer, default=0, nullable=False, comment='Block2 시작 시 Block1 자동 종료 (0=false, 1=true)')

    # 시스템
    block1_min_start_interval_days = Column(Integer, default=20, nullable=False, comment='같은 레벨 블록 중복 방지: 시작 후 N일간 새 블록 탐지 금지')

    # Block2 추가 조건
    block2_volume_ratio = Column(Float, comment='Seed Block1 최고 거래량 대비 비율 (%)')
    block2_low_price_margin = Column(Float, comment='Seed Block1 최고가 저가 마진 (%)')
    block2_min_candles_after_block1 = Column(Integer, comment='Seed Block1 시작 후 최소 캔들 수')
    block2_max_candles_after_block1 = Column(Integer, nullable=True, comment='Seed Block1 시작 후 최대 캔들 수')

    # Block3 추가 조건
    block3_volume_ratio = Column(Float, comment='Seed Block2 최고 거래량 대비 비율 (%)')
    block3_low_price_margin = Column(Float, comment='Seed Block2 최고가 저가 마진 (%)')
    block3_min_candles_after_block2 = Column(Integer, comment='Seed Block2 시작 후 최소 캔들 수')
    block3_max_candles_after_block2 = Column(Integer, nullable=True, comment='Seed Block2 시작 후 최대 캔들 수')

    # Block4 추가 조건
    block4_volume_ratio = Column(Float, comment='Seed Block3 최고 거래량 대비 비율 (%)')
    block4_low_price_margin = Column(Float, comment='Seed Block3 최고가 저가 마진 (%)')
    block4_min_candles_after_block3 = Column(Integer, comment='Seed Block3 시작 후 최소 캔들 수')
    block4_max_candles_after_block3 = Column(Integer, nullable=True, comment='Seed Block3 시작 후 최대 캔들 수')

    # Block2 전용 파라미터 (Optional)
    block2_entry_surge_rate = Column(Float, comment='Block2 전용 진입 급등률 (%)')
    block2_entry_ma_period = Column(Integer, comment='Block2 전용 진입 이동평균선 기간')
    block2_entry_max_deviation_ratio = Column(Float, comment='Block2 전용 최대 이격도 비율')
    block2_entry_min_trading_value = Column(Float, comment='Block2 전용 최소 거래대금 (억원)')
    block2_entry_volume_high_days = Column(Integer, comment='Block2 전용 N일 신고거래량 (달력 기준)')
    block2_entry_volume_spike_ratio = Column(Float, comment='Block2 전용 전날 대비 거래량 비율 (%)')
    block2_entry_price_high_days = Column(Integer, comment='Block2 전용 N일 신고가 (달력 기준)')
    block2_exit_condition_type = Column(String(50), comment='Block2 전용 종료 조건 타입')
    block2_exit_ma_period = Column(Integer, comment='Block2 전용 종료용 이동평균선 기간')
    block2_auto_exit_on_next_block = Column(Integer, default=0, nullable=False, comment='Block3 시작 시 Block2 자동 종료 (0=false, 1=true)')
    block2_min_start_interval_days = Column(Integer, comment='Block2 전용: 같은 레벨 블록 중복 방지 (시작 후 N일간)')

    # Block3 전용 파라미터 (Optional)
    block3_entry_surge_rate = Column(Float, comment='Block3 전용 진입 급등률 (%)')
    block3_entry_ma_period = Column(Integer, comment='Block3 전용 진입 이동평균선 기간')
    block3_entry_max_deviation_ratio = Column(Float, comment='Block3 전용 최대 이격도 비율')
    block3_entry_min_trading_value = Column(Float, comment='Block3 전용 최소 거래대금 (억원)')
    block3_entry_volume_high_days = Column(Integer, comment='Block3 전용 N일 신고거래량 (달력 기준)')
    block3_entry_volume_spike_ratio = Column(Float, comment='Block3 전용 전날 대비 거래량 비율 (%)')
    block3_entry_price_high_days = Column(Integer, comment='Block3 전용 N일 신고가 (달력 기준)')
    block3_exit_condition_type = Column(String(50), comment='Block3 전용 종료 조건 타입')
    block3_exit_ma_period = Column(Integer, comment='Block3 전용 종료용 이동평균선 기간')
    block3_auto_exit_on_next_block = Column(Integer, default=0, nullable=False, comment='Block4 시작 시 Block3 자동 종료 (0=false, 1=true)')
    block3_min_start_interval_days = Column(Integer, comment='Block3 전용: 같은 레벨 블록 중복 방지 (시작 후 N일간)')

    # Block4 전용 파라미터 (Optional)
    block4_entry_surge_rate = Column(Float, comment='Block4 전용 진입 급등률 (%)')
    block4_entry_ma_period = Column(Integer, comment='Block4 전용 진입 이동평균선 기간')
    block4_entry_max_deviation_ratio = Column(Float, comment='Block4 전용 최대 이격도 비율')
    block4_entry_min_trading_value = Column(Float, comment='Block4 전용 최소 거래대금 (억원)')
    block4_entry_volume_high_days = Column(Integer, comment='Block4 전용 N일 신고거래량 (달력 기준)')
    block4_entry_volume_spike_ratio = Column(Float, comment='Block4 전용 전날 대비 거래량 비율 (%)')
    block4_entry_price_high_days = Column(Integer, comment='Block4 전용 N일 신고가 (달력 기준)')
    block4_exit_condition_type = Column(String(50), comment='Block4 전용 종료 조건 타입')
    block4_exit_ma_period = Column(Integer, comment='Block4 전용 종료용 이동평균선 기간')
    block4_auto_exit_on_next_block = Column(Integer, default=0, nullable=False, comment='일관성을 위해 포함 (Block5 없음, 실제 작동 안 함)')
    block4_min_start_interval_days = Column(Integer, comment='Block4 전용: 같은 레벨 블록 중복 방지 (시작 후 N일간)')

    # 메타데이터
    is_active = Column(Integer, default=1, comment='활성 여부')
    created_at = Column(DateTime, default=datetime.now, comment='생성일시')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='수정일시')

    # 인덱스
    __table_args__ = (
        Index('ix_redetection_condition_name', 'name', unique=True),
        Index('ix_redetection_condition_active', 'is_active'),
    )

    def __repr__(self):
        return f"<RedetectionConditionPreset(name={self.name}, surge_rate={self.block1_entry_surge_rate}%, tol={self.block1_tolerance_pct}%)>"
