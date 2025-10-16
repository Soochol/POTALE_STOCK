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
