"""
Stock-related Database Models
주식 기본 정보 및 가격 데이터 모델
"""
from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, Float, String, Date, DateTime, Index, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


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
