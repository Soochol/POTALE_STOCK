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
    block1_entry_surge_rate = Column(Float, nullable=False, comment='진입 급등률 (%)')
    block1_entry_ma_period = Column(Integer, nullable=False, comment='진입 이동평균선 기간')
    block1_entry_high_above_ma = Column(Integer, default=1, comment='고가가 이평선 위에 있어야 함')
    block1_entry_max_deviation_ratio = Column(Float, nullable=False, comment='최대 이격도 비율')
    block1_entry_min_trading_value = Column(Float, nullable=False, comment='최소 거래대금 (억원)')
    block1_entry_volume_high_months = Column(Integer, nullable=True, comment='N개월 신고거래량 (None=조건 비활성화)')
    block1_entry_volume_spike_ratio = Column(Float, nullable=False, comment='전날 대비 거래량 비율 (%)')
    block1_entry_price_high_months = Column(Integer, nullable=True, comment='N개월 신고가 (None=조건 비활성화)')

    # 종료 조건
    block1_exit_condition_type = Column(String(50), nullable=False, comment='종료 조건 타입')
    block1_exit_ma_period = Column(Integer, comment='종료용 이동평균선 기간')

    # 시스템
    block1_cooldown_days = Column(Integer, default=20, nullable=False, comment='Seed 간 최소 간격 (일)')

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
    block2_entry_high_above_ma = Column(Integer, comment='Block2 전용 고가≥이평선')
    block2_entry_max_deviation_ratio = Column(Float, comment='Block2 전용 최대 이격도')
    block2_entry_min_trading_value = Column(Float, comment='Block2 전용 최소 거래대금')
    block2_entry_volume_high_months = Column(Integer, comment='Block2 전용 N개월 신고거래량')
    block2_entry_volume_spike_ratio = Column(Float, comment='Block2 전용 거래량 비율')
    block2_entry_price_high_months = Column(Integer, comment='Block2 전용 N개월 신고가')
    block2_exit_condition_type = Column(String(50), comment='Block2 전용 종료 조건 타입')
    block2_exit_ma_period = Column(Integer, comment='Block2 전용 종료 이평선 기간')
    block2_cooldown_days = Column(Integer, comment='Block2 전용 Cooldown (일)')

    # Block3 전용 파라미터 (Optional)
    block3_entry_surge_rate = Column(Float, comment='Block3 전용 진입 급등률 (%)')
    block3_entry_ma_period = Column(Integer, comment='Block3 전용 진입 이동평균선 기간')
    block3_entry_high_above_ma = Column(Integer, comment='Block3 전용 고가≥이평선')
    block3_entry_max_deviation_ratio = Column(Float, comment='Block3 전용 최대 이격도')
    block3_entry_min_trading_value = Column(Float, comment='Block3 전용 최소 거래대금')
    block3_entry_volume_high_months = Column(Integer, comment='Block3 전용 N개월 신고거래량')
    block3_entry_volume_spike_ratio = Column(Float, comment='Block3 전용 거래량 비율')
    block3_entry_price_high_months = Column(Integer, comment='Block3 전용 N개월 신고가')
    block3_exit_condition_type = Column(String(50), comment='Block3 전용 종료 조건 타입')
    block3_exit_ma_period = Column(Integer, comment='Block3 전용 종료 이평선 기간')
    block3_cooldown_days = Column(Integer, comment='Block3 전용 Cooldown (일)')

    # Block4 전용 파라미터 (Optional)
    block4_entry_surge_rate = Column(Float, comment='Block4 전용 진입 급등률 (%)')
    block4_entry_ma_period = Column(Integer, comment='Block4 전용 진입 이동평균선 기간')
    block4_entry_high_above_ma = Column(Integer, comment='Block4 전용 고가≥이평선')
    block4_entry_max_deviation_ratio = Column(Float, comment='Block4 전용 최대 이격도')
    block4_entry_min_trading_value = Column(Float, comment='Block4 전용 최소 거래대금')
    block4_entry_volume_high_months = Column(Integer, comment='Block4 전용 N개월 신고거래량')
    block4_entry_volume_spike_ratio = Column(Float, comment='Block4 전용 거래량 비율')
    block4_entry_price_high_months = Column(Integer, comment='Block4 전용 N개월 신고가')
    block4_exit_condition_type = Column(String(50), comment='Block4 전용 종료 조건 타입')
    block4_exit_ma_period = Column(Integer, comment='Block4 전용 종료 이평선 기간')
    block4_cooldown_days = Column(Integer, comment='Block4 전용 Cooldown (일)')

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
    block1_entry_surge_rate = Column(Float, nullable=False, comment='진입 급등률 (%) - 완화')
    block1_entry_ma_period = Column(Integer, nullable=False, comment='진입 이동평균선 기간')
    block1_entry_high_above_ma = Column(Integer, default=1, comment='고가가 이평선 위에 있어야 함')
    block1_entry_max_deviation_ratio = Column(Float, nullable=False, comment='최대 이격도 비율')
    block1_entry_min_trading_value = Column(Float, nullable=False, comment='최소 거래대금 (억원)')
    block1_entry_volume_high_months = Column(Integer, nullable=True, comment='N개월 신고거래량 (None=조건 비활성화)')
    block1_entry_volume_spike_ratio = Column(Float, nullable=False, comment='전날 대비 거래량 비율 (%) - 완화')
    block1_entry_price_high_months = Column(Integer, nullable=True, comment='N개월 신고가 (None=조건 비활성화)')

    # 재탐지 전용: 가격 범위 Tolerance
    block1_tolerance_pct = Column(Float, nullable=False, default=10.0, comment='Block1 재탐지 가격 범위 (±%)')
    block2_tolerance_pct = Column(Float, nullable=False, default=15.0, comment='Block2 재탐지 가격 범위 (±%)')
    block3_tolerance_pct = Column(Float, nullable=False, default=20.0, comment='Block3 재탐지 가격 범위 (±%)')
    block4_tolerance_pct = Column(Float, nullable=False, default=25.0, comment='Block4 재탐지 가격 범위 (±%)')

    # 종료 조건
    block1_exit_condition_type = Column(String(50), nullable=False, comment='종료 조건 타입')
    block1_exit_ma_period = Column(Integer, comment='종료용 이동평균선 기간')

    # 시스템
    block1_cooldown_days = Column(Integer, default=20, nullable=False, comment='재탐지 간 최소 간격 (일)')

    # Block2 추가 조건
    block2_volume_ratio = Column(Float, comment='Block1 최고 거래량 대비 비율 (%)')
    block2_low_price_margin = Column(Float, comment='Block1 최고가 저가 마진 (%)')

    # Block3 추가 조건
    block3_volume_ratio = Column(Float, comment='Block2 최고 거래량 대비 비율 (%)')
    block3_low_price_margin = Column(Float, comment='Block2 최고가 저가 마진 (%)')

    # Block4 추가 조건
    block4_volume_ratio = Column(Float, comment='Block3 최고 거래량 대비 비율 (%)')
    block4_low_price_margin = Column(Float, comment='Block3 최고가 저가 마진 (%)')

    # Block2 전용 파라미터 (Optional)
    block2_entry_surge_rate = Column(Float, comment='Block2 전용 진입 급등률 (%)')
    block2_entry_ma_period = Column(Integer, comment='Block2 전용 진입 이동평균선 기간')
    block2_entry_high_above_ma = Column(Integer, comment='Block2 전용 고가>=이평선')
    block2_entry_max_deviation_ratio = Column(Float, comment='Block2 전용 최대 이격도 비율')
    block2_entry_min_trading_value = Column(Float, comment='Block2 전용 최소 거래대금 (억원)')
    block2_entry_volume_high_months = Column(Integer, comment='Block2 전용 N개월 신고거래량')
    block2_entry_volume_spike_ratio = Column(Float, comment='Block2 전용 전날 대비 거래량 비율 (%)')
    block2_entry_price_high_months = Column(Integer, comment='Block2 전용 N개월 신고가')
    block2_exit_condition_type = Column(String(50), comment='Block2 전용 종료 조건 타입')
    block2_exit_ma_period = Column(Integer, comment='Block2 전용 종료용 이동평균선 기간')
    block2_cooldown_days = Column(Integer, comment='Block2 전용 재탐지 간 최소 간격 (일)')

    # Block3 전용 파라미터 (Optional)
    block3_entry_surge_rate = Column(Float, comment='Block3 전용 진입 급등률 (%)')
    block3_entry_ma_period = Column(Integer, comment='Block3 전용 진입 이동평균선 기간')
    block3_entry_high_above_ma = Column(Integer, comment='Block3 전용 고가>=이평선')
    block3_entry_max_deviation_ratio = Column(Float, comment='Block3 전용 최대 이격도 비율')
    block3_entry_min_trading_value = Column(Float, comment='Block3 전용 최소 거래대금 (억원)')
    block3_entry_volume_high_months = Column(Integer, comment='Block3 전용 N개월 신고거래량')
    block3_entry_volume_spike_ratio = Column(Float, comment='Block3 전용 전날 대비 거래량 비율 (%)')
    block3_entry_price_high_months = Column(Integer, comment='Block3 전용 N개월 신고가')
    block3_exit_condition_type = Column(String(50), comment='Block3 전용 종료 조건 타입')
    block3_exit_ma_period = Column(Integer, comment='Block3 전용 종료용 이동평균선 기간')
    block3_cooldown_days = Column(Integer, comment='Block3 전용 재탐지 간 최소 간격 (일)')

    # Block4 전용 파라미터 (Optional)
    block4_entry_surge_rate = Column(Float, comment='Block4 전용 진입 급등률 (%)')
    block4_entry_ma_period = Column(Integer, comment='Block4 전용 진입 이동평균선 기간')
    block4_entry_high_above_ma = Column(Integer, comment='Block4 전용 고가>=이평선')
    block4_entry_max_deviation_ratio = Column(Float, comment='Block4 전용 최대 이격도 비율')
    block4_entry_min_trading_value = Column(Float, comment='Block4 전용 최소 거래대금 (억원)')
    block4_entry_volume_high_months = Column(Integer, comment='Block4 전용 N개월 신고거래량')
    block4_entry_volume_spike_ratio = Column(Float, comment='Block4 전용 전날 대비 거래량 비율 (%)')
    block4_entry_price_high_months = Column(Integer, comment='Block4 전용 N개월 신고가')
    block4_exit_condition_type = Column(String(50), comment='Block4 전용 종료 조건 타입')
    block4_exit_ma_period = Column(Integer, comment='Block4 전용 종료용 이동평균선 기간')
    block4_cooldown_days = Column(Integer, comment='Block4 전용 재탐지 간 최소 간격 (일)')

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
