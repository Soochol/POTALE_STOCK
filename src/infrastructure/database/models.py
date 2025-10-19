"""
SQLAlchemy Database Models
"""
from datetime import date, datetime
from sqlalchemy import Column, Integer, BigInteger, Float, String, Date, DateTime, Index, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class StockInfo(Base):
    """종목 정보 테이블"""
    __tablename__ = 'stock_info'

    ticker = Column(String(10), primary_key=True, comment='종목코드')
    name = Column(String(100), nullable=False, comment='종목명')
    market = Column(String(10), nullable=False, comment='시장구분 (KOSPI, KOSDAQ)')
    sector = Column(String(50), comment='업종')
    sector_code = Column(String(10), comment='업종코드')
    listing_date = Column(Date, comment='상장일')
    is_active = Column(Integer, default=1, comment='활성 여부 (1: 활성, 0: 비활성)')
    delisting_date = Column(Date, comment='상장폐지일')
    listing_shares = Column(BigInteger, comment='상장주식수')

    created_at = Column(DateTime, default=datetime.now, comment='생성일시')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='수정일시')

    # 관계 설정
    prices = relationship("StockPrice", back_populates="stock_info", cascade="all, delete-orphan")
    market_data = relationship("MarketData", back_populates="stock_info", cascade="all, delete-orphan")
    investor_trading = relationship("InvestorTrading", back_populates="stock_info", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<StockInfo(ticker={self.ticker}, name={self.name})>"


class StockPrice(Base):
    """주식 가격 테이블 (OHLCV) - 하이브리드 수집 (수정주가+수정거래량)"""
    __tablename__ = 'stock_price'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), ForeignKey('stock_info.ticker'), nullable=False, comment='종목코드')
    date = Column(Date, nullable=False, comment='날짜')

    # 수정주가 (액면분할/병합 반영)
    open = Column(Float, nullable=False, comment='시가 (수정주가)')
    high = Column(Float, nullable=False, comment='고가 (수정주가)')
    low = Column(Float, nullable=False, comment='저가 (수정주가)')
    close = Column(Float, nullable=False, comment='종가 (수정주가)')
    volume = Column(BigInteger, nullable=False, comment='거래량 (수정거래량)')

    # 추가 지표들
    change_rate = Column(Float, comment='등락률')
    trading_value = Column(BigInteger, comment='거래대금 (수정종가 × 수정거래량)')

    # 하이브리드 수집 추가 필드 (참고용)
    adjustment_ratio = Column(Float, comment='조정 비율 (원본종가/수정종가)')
    raw_close = Column(Float, comment='원본 종가 (참고용)')
    raw_volume = Column(BigInteger, comment='원본 거래량 (참고용)')

    created_at = Column(DateTime, default=datetime.now, comment='생성일시')

    # 관계 설정
    stock_info = relationship("StockInfo", back_populates="prices")

    # 복합 인덱스 (종목코드 + 날짜)
    __table_args__ = (
        Index('ix_stock_price_ticker_date', 'ticker', 'date', unique=True),
        Index('ix_stock_price_date', 'date'),
    )

    def __repr__(self):
        return f"<StockPrice(ticker={self.ticker}, date={self.date}, close={self.close})>"


class MarketData(Base):
    """시장 데이터 테이블 (시가총액, PER, PBR 등)"""
    __tablename__ = 'market_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), ForeignKey('stock_info.ticker'), nullable=False, comment='종목코드')
    date = Column(Date, nullable=False, comment='날짜')

    market_cap = Column(BigInteger, comment='시가총액')
    per = Column(Float, comment='PER (주가수익비율)')
    pbr = Column(Float, comment='PBR (주가순자산비율)')
    eps = Column(Float, comment='EPS (주당순이익)')
    bps = Column(Float, comment='BPS (주당순자산)')
    div = Column(Float, comment='배당수익률')
    dps = Column(Float, comment='주당배당금')

    created_at = Column(DateTime, default=datetime.now, comment='생성일시')

    # 관계 설정
    stock_info = relationship("StockInfo", back_populates="market_data")

    # 복합 인덱스
    __table_args__ = (
        Index('ix_market_data_ticker_date', 'ticker', 'date', unique=True),
        Index('ix_market_data_date', 'date'),
        Index('ix_market_data_market_cap', 'market_cap'),
    )

    def __repr__(self):
        return f"<MarketData(ticker={self.ticker}, date={self.date}, market_cap={self.market_cap})>"


class InvestorTrading(Base):
    """투자자별 거래 테이블"""
    __tablename__ = 'investor_trading'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), ForeignKey('stock_info.ticker'), nullable=False, comment='종목코드')
    date = Column(Date, nullable=False, comment='날짜')

    # 순매수 (순매수 = 매수 - 매도)
    institution_net_buy = Column(BigInteger, default=0, comment='기관 순매수')
    foreign_net_buy = Column(BigInteger, default=0, comment='외국인 순매수')
    individual_net_buy = Column(BigInteger, default=0, comment='개인 순매수')

    # 매수/매도 금액 (선택적)
    institution_buy = Column(BigInteger, comment='기관 매수금액')
    institution_sell = Column(BigInteger, comment='기관 매도금액')
    foreign_buy = Column(BigInteger, comment='외국인 매수금액')
    foreign_sell = Column(BigInteger, comment='외국인 매도금액')
    individual_buy = Column(BigInteger, comment='개인 매수금액')
    individual_sell = Column(BigInteger, comment='개인 매도금액')

    created_at = Column(DateTime, default=datetime.now, comment='생성일시')

    # 관계 설정
    stock_info = relationship("StockInfo", back_populates="investor_trading")

    # 복합 인덱스
    __table_args__ = (
        Index('ix_investor_trading_ticker_date', 'ticker', 'date', unique=True),
        Index('ix_investor_trading_date', 'date'),
        Index('ix_investor_trading_foreign', 'foreign_net_buy'),
        Index('ix_investor_trading_institution', 'institution_net_buy'),
    )

    def __repr__(self):
        return f"<InvestorTrading(ticker={self.ticker}, date={self.date}, foreign_net={self.foreign_net_buy})>"


class DataCollectionLog(Base):
    """데이터 수집 로그 테이블"""
    __tablename__ = 'data_collection_log'

    id = Column(Integer, primary_key=True, autoincrement=True)
    collection_type = Column(String(50), nullable=False, comment='수집 타입 (price, market_data, etc)')
    ticker = Column(String(10), comment='종목코드 (전체 수집시 NULL)')
    start_date = Column(Date, comment='수집 시작일')
    end_date = Column(Date, comment='수집 종료일')

    status = Column(String(20), nullable=False, comment='상태 (success, failed, partial)')
    record_count = Column(Integer, default=0, comment='수집된 레코드 수')
    error_message = Column(String(500), comment='에러 메시지')

    started_at = Column(DateTime, nullable=False, comment='수집 시작 시각')
    completed_at = Column(DateTime, comment='수집 완료 시각')
    duration_seconds = Column(Float, comment='소요 시간(초)')

    # 인덱스
    __table_args__ = (
        Index('ix_collection_log_date', 'started_at'),
        Index('ix_collection_log_ticker', 'ticker'),
    )

    def __repr__(self):
        return f"<DataCollectionLog(type={self.collection_type}, ticker={self.ticker}, status={self.status})>"


class CollectionProgress(Base):
    """수집 진행 상황 추적 테이블"""
    __tablename__ = 'collection_progress'

    id = Column(Integer, primary_key=True, autoincrement=True)
    collection_type = Column(String(50), nullable=False, comment='수집 타입 (price, market_data, investor_trading, etc)')
    target_date = Column(Date, nullable=False, comment='수집 대상 날짜')
    status = Column(String(20), default='pending', comment='상태 (pending, in_progress, completed, failed)')

    ticker = Column(String(10), comment='종목코드 (개별 수집 시)')
    record_count = Column(Integer, default=0, comment='수집된 레코드 수')
    error_message = Column(String(500), comment='에러 메시지')

    started_at = Column(DateTime, comment='수집 시작 시각')
    completed_at = Column(DateTime, comment='수집 완료 시각')
    retry_count = Column(Integer, default=0, comment='재시도 횟수')

    created_at = Column(DateTime, default=datetime.now, comment='생성일시')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='수정일시')

    # 인덱스
    __table_args__ = (
        Index('ix_collection_progress_type_date', 'collection_type', 'target_date', unique=True),
        Index('ix_collection_progress_status', 'status'),
        Index('ix_collection_progress_date', 'target_date'),
    )

    def __repr__(self):
        return f"<CollectionProgress(type={self.collection_type}, date={self.target_date}, status={self.status})>"


class DataQualityCheck(Base):
    """데이터 품질 체크 테이블"""
    __tablename__ = 'data_quality_check'

    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String(50), nullable=False, comment='테이블명')
    check_date = Column(Date, nullable=False, comment='체크 날짜')
    check_type = Column(String(50), nullable=False, comment='체크 타입 (missing_data, duplicate, outlier, etc)')

    status = Column(String(20), nullable=False, comment='상태 (pass, warning, fail)')
    issue_count = Column(Integer, default=0, comment='발견된 이슈 수')
    details = Column(String(1000), comment='상세 내용 (JSON 형식)')

    checked_at = Column(DateTime, default=datetime.now, comment='체크 시각')

    # 인덱스
    __table_args__ = (
        Index('ix_data_quality_table_date', 'table_name', 'check_date'),
        Index('ix_data_quality_status', 'status'),
    )

    def __repr__(self):
        return f"<DataQualityCheck(table={self.table_name}, date={self.check_date}, status={self.status})>"




class Block1ConditionPreset(Base):
    """블록1 조건 프리셋 테이블"""
    __tablename__ = 'block1_condition_preset'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, comment='조건 프리셋 이름')
    description = Column(String(500), comment='조건 설명')

    # 진입 조건 1: 등락률
    entry_surge_rate = Column(Float, comment='진입 급등률 (%)')

    # 진입 조건 2: 이평선 위치
    entry_ma_period = Column(Integer, comment='진입 이동평균선 기간')
    entry_high_above_ma = Column(Integer, comment='고가가 이평선 위에 있어야 함 (1: True, 0: False, NULL: None)')

    # 진입 조건 3: 이격도
    entry_max_deviation_ratio = Column(Float, comment='최대 이격도 비율 (%)')

    # 진입 조건 4: 거래대금
    entry_min_trading_value = Column(Float, comment='최소 거래대금 (억원)')

    # 진입 조건 5: 거래량 신고 (N개월 신고거래량)
    entry_volume_high_months = Column(Integer, comment='N개월 신고거래량')

    # 진입 조건 6: 전날 거래량 급증
    entry_volume_spike_ratio = Column(Float, comment='전날 대비 거래량 급증 비율 (%)')

    # 진입 조건 7: 가격 신고 (N개월 신고가)
    entry_price_high_months = Column(Integer, comment='N개월 신고가')

    # 종료 조건
    exit_condition_type = Column(String(50), nullable=False, comment='종료 조건 타입 (ma_break, three_line_reversal, body_middle)')
    exit_ma_period = Column(Integer, comment='종료용 이동평균선 기간')

    # 중복 탐지 방지
    cooldown_days = Column(Integer, default=120, nullable=False, comment='쿨다운 기간 (일)')

    # 메타데이터
    is_active = Column(Integer, default=1, comment='활성 여부 (1: 활성, 0: 비활성)')
    created_at = Column(DateTime, default=datetime.now, comment='생성일시')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='수정일시')

    # 인덱스
    __table_args__ = (
        Index('ix_block1_condition_name', 'name', unique=True),
        Index('ix_block1_condition_active', 'is_active'),
    )

    def __repr__(self):
        return f"<Block1ConditionPreset(name={self.name}, entry_ma_period={self.entry_ma_period})>"


class Block2ConditionPreset(Base):
    """블록2 조건 프리셋 테이블"""
    __tablename__ = 'block2_condition_preset'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, comment='조건 프리셋 이름')
    description = Column(String(500), comment='조건 설명')

    # Block1 조건 (상속, 값은 다를 수 있음)
    entry_surge_rate = Column(Float, comment='진입 급등률 (%)')
    entry_ma_period = Column(Integer, comment='진입 이동평균선 기간')
    entry_high_above_ma = Column(Integer, comment='고가가 이평선 위에 있어야 함')
    entry_max_deviation_ratio = Column(Float, comment='최대 이격도 비율 (%)')
    entry_min_trading_value = Column(Float, comment='최소 거래대금 (억원)')
    entry_volume_high_months = Column(Integer, comment='N개월 신고거래량')
    entry_volume_spike_ratio = Column(Float, comment='전날 대비 거래량 급증 비율 (%)')
    entry_price_high_months = Column(Integer, comment='N개월 신고가')
    exit_condition_type = Column(String(50), nullable=False, comment='종료 조건 타입')
    exit_ma_period = Column(Integer, comment='종료용 이동평균선 기간')

    # Block2 추가 조건
    block_volume_ratio = Column(Float, comment='블록1 최고 거래량 대비 비율 (%, 예: 15 = 15%)')
    low_price_margin = Column(Float, comment='저가 마진 (%, 예: 10 = 10%)')

    # 중복 탐지 방지
    cooldown_days = Column(Integer, default=20, nullable=False, comment='쿨다운 기간 (일)')

    # Block 전환 조건
    min_candles_after_block1 = Column(Integer, comment='Block1 시작 후 최소 캔들 수 (예: 4 = 5번째 캔들부터)')

    # 메타데이터
    is_active = Column(Integer, default=1, comment='활성 여부 (1: 활성, 0: 비활성)')
    created_at = Column(DateTime, default=datetime.now, comment='생성일시')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='수정일시')

    # 인덱스
    __table_args__ = (
        Index('ix_block2_condition_name', 'name', unique=True),
        Index('ix_block2_condition_active', 'is_active'),
    )

    def __repr__(self):
        return f"<Block2ConditionPreset(name={self.name}, entry_surge_rate={self.entry_surge_rate})>"


class Block3ConditionPreset(Base):
    """블록3 조건 프리셋 테이블"""
    __tablename__ = 'block3_condition_preset'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, comment='조건 프리셋 이름')
    description = Column(String(500), comment='조건 설명')

    # Block1 조건 (상속, Block2에서도 상속받았지만 Block3에서 다시 정의 가능)
    entry_surge_rate = Column(Float, comment='진입 급등률 (%)')
    entry_ma_period = Column(Integer, comment='진입 이동평균선 기간')
    entry_high_above_ma = Column(Integer, comment='고가가 이평선 위에 있어야 함')
    entry_max_deviation_ratio = Column(Float, comment='최대 이격도 비율 (%)')
    entry_min_trading_value = Column(Float, comment='최소 거래대금 (억원)')
    entry_volume_high_months = Column(Integer, comment='N개월 신고거래량')
    entry_volume_spike_ratio = Column(Float, comment='전날 대비 거래량 급증 비율 (%)')
    entry_price_high_months = Column(Integer, comment='N개월 신고가')
    exit_condition_type = Column(String(50), nullable=False, comment='종료 조건 타입')
    exit_ma_period = Column(Integer, comment='종료용 이동평균선 기간')

    # Block2 추가 조건 (상속)
    block2_volume_ratio = Column(Float, comment='블록1 최고 거래량 대비 비율 (%, Block2 조건)')
    block2_low_price_margin = Column(Float, comment='저가 마진 (%, Block2 조건)')

    # Block3 추가 조건
    block_volume_ratio = Column(Float, comment='블록2 최고 거래량 대비 비율 (%, 예: 15 = 15%)')
    low_price_margin = Column(Float, comment='저가 마진 (%, 예: 10 = 10%)')

    # 중복 탐지 방지
    cooldown_days = Column(Integer, default=20, nullable=False, comment='쿨다운 기간 (일)')

    # Block 전환 조건
    min_candles_after_block1 = Column(Integer, comment='Block1 시작 후 최소 캔들 수')
    min_candles_after_block2 = Column(Integer, comment='Block2 시작 후 최소 캔들 수 (예: 4 = 5번째 캔들부터)')

    # 메타데이터
    is_active = Column(Integer, default=1, comment='활성 여부 (1: 활성, 0: 비활성)')
    created_at = Column(DateTime, default=datetime.now, comment='생성일시')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='수정일시')

    # 인덱스
    __table_args__ = (
        Index('ix_block3_condition_name', 'name', unique=True),
        Index('ix_block3_condition_active', 'is_active'),
    )

    def __repr__(self):
        return f"<Block3ConditionPreset(name={self.name}, entry_surge_rate={self.entry_surge_rate})>"


class Block1Detection(Base):
    """블록1 탐지 결과 테이블"""
    __tablename__ = 'block1_detection'

    id = Column(Integer, primary_key=True, autoincrement=True)
    block1_id = Column(String(50), unique=True, nullable=False, comment='블록1 고유 ID (UUID)')
    ticker = Column(String(10), ForeignKey('stock_info.ticker'), nullable=False, comment='종목코드')

    # 상태
    status = Column(String(20), nullable=False, default='active', comment='상태 (active, completed)')

    # 시작/종료 날짜
    started_at = Column(Date, nullable=False, comment='블록1 시작일')
    ended_at = Column(Date, comment='블록1 종료일')

    # 진입 시점 OHLC 가격
    entry_open = Column(Float, nullable=False, comment='시작일 시가')
    entry_high = Column(Float, nullable=False, comment='시작일 고가')
    entry_low = Column(Float, nullable=False, comment='시작일 저가')
    entry_close = Column(Float, nullable=False, comment='시작일 종가')

    # 진입 시점 거래 정보
    entry_volume = Column(BigInteger, nullable=False, comment='시작일 거래량')
    entry_trading_value = Column(Float, comment='시작일 거래대금 (억)')

    # 진입 시점 기술적 지표
    entry_ma_value = Column(Float, comment='시작일 이동평균선 값')
    entry_rate = Column(Float, comment='시작일 등락률 (%)')
    entry_deviation = Column(Float, comment='시작일 이격도 (%)')

    # 블록1 기간 중 최고가 추적
    peak_price = Column(Float, comment='블록1 기간 중 최고가')
    peak_date = Column(Date, comment='최고가 달성일')

    # 종료 정보
    exit_reason = Column(String(50), comment='종료 사유 (ma_break, three_line_reversal, body_middle)')
    exit_price = Column(Float, comment='종료일 종가')

    # 메타데이터
    condition_name = Column(String(100), comment='사용된 조건 이름')
    created_at = Column(DateTime, default=datetime.now, comment='레코드 생성일시')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='수정일시')

    # 패턴 재탐지 시스템
    pattern_id = Column(Integer, ForeignKey('block_pattern.pattern_id'), comment='패턴 ID (재탐지 시스템용)')
    detection_type = Column(String(20), comment='탐지 타입 (seed, redetection)')

    # 관계 설정
    stock_info = relationship("StockInfo")
    pattern = relationship("BlockPattern", back_populates="block1_detections", foreign_keys=[pattern_id])

    # 인덱스
    __table_args__ = (
        Index('ix_block1_ticker_started', 'ticker', 'started_at'),
        Index('ix_block1_status', 'status'),
        Index('ix_block1_started', 'started_at'),
        Index('ix_block1_id', 'block1_id', unique=True),
        Index('ix_block1_pattern', 'pattern_id'),
        Index('ix_block1_detection_type', 'detection_type'),
    )

    def __repr__(self):
        return f"<Block1Detection(ticker={self.ticker}, started={self.started_at}, status={self.status})>"


class Block2Detection(Base):
    """블록2 탐지 결과 테이블"""
    __tablename__ = 'block2_detection'

    id = Column(Integer, primary_key=True, autoincrement=True)
    block2_id = Column(String(50), unique=True, nullable=False, comment='블록2 고유 ID (UUID)')
    ticker = Column(String(10), ForeignKey('stock_info.ticker'), nullable=False, comment='종목코드')

    # 상태
    status = Column(String(20), nullable=False, default='active', comment='상태 (active, completed)')

    # 시작/종료 날짜
    started_at = Column(Date, nullable=False, comment='블록2 시작일')
    ended_at = Column(Date, comment='블록2 종료일')

    # 진입 정보
    entry_close = Column(Float, nullable=False, comment='시작일 종가')
    entry_rate = Column(Float, comment='시작일 등락률 (%)')

    # 직전 블록1 정보
    prev_block1_id = Column(Integer, ForeignKey('block1_detection.id'), comment='참조한 블록1 ID')
    prev_block1_peak_price = Column(Float, comment='블록1 최고가')
    prev_block1_peak_volume = Column(BigInteger, comment='블록1 최고 거래량')

    # 블록2 기간 중 최고가/거래량 추적
    peak_price = Column(Float, comment='블록2 기간 중 최고가')
    peak_date = Column(Date, comment='최고가 달성일')
    peak_gain_ratio = Column(Float, comment='최고가 상승률 (%)')
    peak_volume = Column(BigInteger, comment='블록2 기간 중 최고 거래량')

    # 종료 정보
    duration_days = Column(Integer, comment='지속 기간 (일)')
    exit_reason = Column(String(50), comment='종료 사유 (ma_break, three_line_reversal, body_middle, block3_started)')

    # 메타데이터
    condition_name = Column(String(100), comment='사용된 조건 이름')
    created_at = Column(DateTime, default=datetime.now, comment='레코드 생성일시')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='수정일시')

    # 패턴 재탐지 시스템
    pattern_id = Column(Integer, ForeignKey('block_pattern.pattern_id'), comment='패턴 ID (재탐지 시스템용)')
    detection_type = Column(String(20), comment='탐지 타입 (seed, redetection)')

    # 관계 설정
    stock_info = relationship("StockInfo")
    prev_block1 = relationship("Block1Detection", foreign_keys=[prev_block1_id])
    pattern = relationship("BlockPattern", back_populates="block2_detections", foreign_keys=[pattern_id])

    # 인덱스
    __table_args__ = (
        Index('ix_block2_ticker_started', 'ticker', 'started_at'),
        Index('ix_block2_status', 'status'),
        Index('ix_block2_started', 'started_at'),
        Index('ix_block2_id', 'block2_id', unique=True),
        Index('ix_block2_prev_block1', 'prev_block1_id'),
        Index('ix_block2_pattern', 'pattern_id'),
        Index('ix_block2_detection_type', 'detection_type'),
    )

    def __repr__(self):
        return f"<Block2Detection(ticker={self.ticker}, started={self.started_at}, status={self.status})>"


class Block3Detection(Base):
    """블록3 탐지 결과 테이블"""
    __tablename__ = 'block3_detection'

    id = Column(Integer, primary_key=True, autoincrement=True)
    block3_id = Column(String(50), unique=True, nullable=False, comment='블록3 고유 ID (UUID)')
    ticker = Column(String(10), ForeignKey('stock_info.ticker'), nullable=False, comment='종목코드')

    # 상태
    status = Column(String(20), nullable=False, default='active', comment='상태 (active, completed)')

    # 시작/종료 날짜
    started_at = Column(Date, nullable=False, comment='블록3 시작일')
    ended_at = Column(Date, comment='블록3 종료일')

    # 진입 정보
    entry_close = Column(Float, nullable=False, comment='시작일 종가')
    entry_rate = Column(Float, comment='시작일 등락률 (%)')

    # 직전 블록2 정보
    prev_block2_id = Column(Integer, ForeignKey('block2_detection.id'), comment='참조한 블록2 ID')
    prev_block2_peak_price = Column(Float, comment='블록2 최고가')
    prev_block2_peak_volume = Column(BigInteger, comment='블록2 최고 거래량')

    # 블록3 기간 중 최고가/거래량 추적
    peak_price = Column(Float, comment='블록3 기간 중 최고가')
    peak_date = Column(Date, comment='최고가 달성일')
    peak_gain_ratio = Column(Float, comment='최고가 상승률 (%)')
    peak_volume = Column(BigInteger, comment='블록3 기간 중 최고 거래량')

    # 종료 정보
    duration_days = Column(Integer, comment='지속 기간 (일)')
    exit_reason = Column(String(50), comment='종료 사유 (ma_break, three_line_reversal, body_middle)')

    # 메타데이터
    condition_name = Column(String(100), comment='사용된 조건 이름')
    created_at = Column(DateTime, default=datetime.now, comment='레코드 생성일시')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='수정일시')

    # 패턴 재탐지 시스템
    pattern_id = Column(Integer, ForeignKey('block_pattern.pattern_id'), comment='패턴 ID (재탐지 시스템용)')
    detection_type = Column(String(20), comment='탐지 타입 (seed, redetection)')

    # 관계 설정
    stock_info = relationship("StockInfo")
    prev_block2 = relationship("Block2Detection", foreign_keys=[prev_block2_id])
    pattern = relationship("BlockPattern", back_populates="block3_detections", foreign_keys=[pattern_id])

    # 인덱스
    __table_args__ = (
        Index('ix_block3_ticker_started', 'ticker', 'started_at'),
        Index('ix_block3_status', 'status'),
        Index('ix_block3_started', 'started_at'),
        Index('ix_block3_id', 'block3_id', unique=True),
        Index('ix_block3_prev_block2', 'prev_block2_id'),
        Index('ix_block3_pattern', 'pattern_id'),
        Index('ix_block3_detection_type', 'detection_type'),
    )

    def __repr__(self):
        return f"<Block3Detection(ticker={self.ticker}, started={self.started_at}, status={self.status})>"


class BlockPattern(Base):
    """블록 패턴 (재탐지 시스템)"""
    __tablename__ = 'block_pattern'

    pattern_id = Column(Integer, primary_key=True, autoincrement=True, comment='패턴 고유 ID')
    ticker = Column(String(10), ForeignKey('stock_info.ticker'), nullable=False, comment='종목코드')

    # Seed 참조
    seed_block1_id = Column(String(50), ForeignKey('block1_detection.block1_id'), nullable=False, comment='Block1 Seed ID')
    seed_block2_id = Column(String(50), ForeignKey('block2_detection.block2_id'), nullable=False, comment='Block2 Seed ID')
    seed_block3_id = Column(String(50), ForeignKey('block3_detection.block3_id'), nullable=False, comment='Block3 Seed ID')

    # 재탐지 기간
    redetection_start = Column(Date, nullable=False, comment='재탐지 시작일 (Block1 Seed 시작일)')
    redetection_end = Column(Date, nullable=False, comment='재탐지 종료일 (시작일 + 5년)')

    # 메타데이터
    created_at = Column(DateTime, default=datetime.now, comment='패턴 생성일시')

    # 관계 설정
    stock_info = relationship("StockInfo")
    seed_block1 = relationship("Block1Detection", foreign_keys=[seed_block1_id])
    seed_block2 = relationship("Block2Detection", foreign_keys=[seed_block2_id])
    seed_block3 = relationship("Block3Detection", foreign_keys=[seed_block3_id])

    block1_detections = relationship("Block1Detection", back_populates="pattern", foreign_keys="Block1Detection.pattern_id")
    block2_detections = relationship("Block2Detection", back_populates="pattern", foreign_keys="Block2Detection.pattern_id")
    block3_detections = relationship("Block3Detection", back_populates="pattern", foreign_keys="Block3Detection.pattern_id")

    # 인덱스
    __table_args__ = (
        Index('ix_block_pattern_ticker', 'ticker'),
        Index('ix_block_pattern_created', 'created_at'),
        Index('ix_block_pattern_redetection_period', 'redetection_start', 'redetection_end'),
    )

    def __repr__(self):
        return f"<BlockPattern(pattern_id={self.pattern_id}, ticker={self.ticker}, start={self.redetection_start})>"


class SeedConditionPreset(Base):
    """Seed 조건 프리셋 테이블 (엄격한 조건)"""
    __tablename__ = 'seed_condition_preset'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, comment='프리셋 이름')
    description = Column(String(500), comment='프리셋 설명')

    # Block1 진입 조건
    entry_surge_rate = Column(Float, nullable=False, comment='진입 급등률 (%)')
    entry_ma_period = Column(Integer, nullable=False, comment='진입 이동평균선 기간')
    entry_high_above_ma = Column(Integer, default=1, comment='고가가 이평선 위에 있어야 함')
    entry_max_deviation_ratio = Column(Float, nullable=False, comment='최대 이격도 비율')
    entry_min_trading_value = Column(Float, nullable=False, comment='최소 거래대금 (억원)')
    entry_volume_high_months = Column(Integer, nullable=False, comment='N개월 신고거래량')
    entry_volume_spike_ratio = Column(Float, nullable=False, comment='전날 대비 거래량 비율 (%)')
    entry_price_high_months = Column(Integer, nullable=False, comment='N개월 신고가')

    # 종료 조건
    exit_condition_type = Column(String(50), nullable=False, comment='종료 조건 타입')
    exit_ma_period = Column(Integer, comment='종료용 이동평균선 기간')

    # 시스템
    cooldown_days = Column(Integer, default=20, nullable=False, comment='Seed 간 최소 간격 (일)')

    # Block2 추가 조건
    block2_volume_ratio = Column(Float, comment='Block1 최고 거래량 대비 비율 (%)')
    block2_low_price_margin = Column(Float, comment='Block1 최고가 저가 마진 (%)')
    block2_min_candles_after_block1 = Column(Integer, comment='Block1 시작 후 최소 캔들 수')

    # Block3 추가 조건
    block3_volume_ratio = Column(Float, comment='Block2 최고 거래량 대비 비율 (%)')
    block3_low_price_margin = Column(Float, comment='Block2 최고가 저가 마진 (%)')
    block3_min_candles_after_block2 = Column(Integer, comment='Block2 시작 후 최소 캔들 수')

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
        return f"<SeedConditionPreset(name={self.name}, surge_rate={self.entry_surge_rate}%)>"


class RedetectionConditionPreset(Base):
    """재탐지 조건 프리셋 테이블 (완화된 조건 + 가격 범위)"""
    __tablename__ = 'redetection_condition_preset'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, comment='프리셋 이름')
    description = Column(String(500), comment='프리셋 설명')

    # Block1 진입 조건 (완화)
    entry_surge_rate = Column(Float, nullable=False, comment='진입 급등률 (%) - 완화')
    entry_ma_period = Column(Integer, nullable=False, comment='진입 이동평균선 기간')
    entry_high_above_ma = Column(Integer, default=1, comment='고가가 이평선 위에 있어야 함')
    entry_max_deviation_ratio = Column(Float, nullable=False, comment='최대 이격도 비율')
    entry_min_trading_value = Column(Float, nullable=False, comment='최소 거래대금 (억원)')
    entry_volume_high_months = Column(Integer, nullable=False, comment='N개월 신고거래량 - 완화')
    entry_volume_spike_ratio = Column(Float, nullable=False, comment='전날 대비 거래량 비율 (%) - 완화')
    entry_price_high_months = Column(Integer, nullable=False, comment='N개월 신고가 - 완화')

    # 재탐지 전용: 가격 범위 Tolerance
    block1_tolerance_pct = Column(Float, nullable=False, default=10.0, comment='Block1 재탐지 가격 범위 (±%)')
    block2_tolerance_pct = Column(Float, nullable=False, default=15.0, comment='Block2 재탐지 가격 범위 (±%)')
    block3_tolerance_pct = Column(Float, nullable=False, default=20.0, comment='Block3 재탐지 가격 범위 (±%)')

    # 종료 조건
    exit_condition_type = Column(String(50), nullable=False, comment='종료 조건 타입')
    exit_ma_period = Column(Integer, comment='종료용 이동평균선 기간')

    # 시스템
    cooldown_days = Column(Integer, default=20, nullable=False, comment='재탐지 간 최소 간격 (일)')

    # Block2 추가 조건
    block2_volume_ratio = Column(Float, comment='Block1 최고 거래량 대비 비율 (%)')
    block2_low_price_margin = Column(Float, comment='Block1 최고가 저가 마진 (%)')
    block2_min_candles_after_block1 = Column(Integer, comment='Block1 시작 후 최소 캔들 수')

    # Block3 추가 조건
    block3_volume_ratio = Column(Float, comment='Block2 최고 거래량 대비 비율 (%)')
    block3_low_price_margin = Column(Float, comment='Block2 최고가 저가 마진 (%)')
    block3_min_candles_after_block2 = Column(Integer, comment='Block2 시작 후 최소 캔들 수')

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
        return f"<RedetectionConditionPreset(name={self.name}, surge_rate={self.entry_surge_rate}%, tol={self.block1_tolerance_pct}%)>"
