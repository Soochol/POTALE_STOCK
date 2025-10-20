"""
Indicator Calculator Service - 기술적 지표 계산 서비스
"""
from src.domain.entities import Stock
from typing import List, Dict
import pandas as pd

class IndicatorCalculator:
    """기술적 지표 계산 서비스"""

    def calculate(self, stocks: List[Stock]) -> List[Stock]:
        """
        주식 데이터에 기술적 지표 추가

        Args:
            stocks: 주식 데이터 리스트

        Returns:
            지표가 추가된 주식 데이터 리스트
        """
        if not stocks:
            return []

        # Stock 리스트를 DataFrame으로 변환
        df = self._stocks_to_dataframe(stocks)

        # 지표 계산
        df = self._calculate_ma(df)
        df = self._calculate_rsi(df)
        df = self._calculate_macd(df)
        df = self._calculate_bollinger_bands(df)
        df = self._calculate_volume_ma(df)

        # DataFrame을 Stock 리스트로 변환
        return self._dataframe_to_stocks(df, stocks)

    def _stocks_to_dataframe(self, stocks: List[Stock]) -> pd.DataFrame:
        """Stock 리스트를 DataFrame으로 변환"""
        data = {
            'date': [s.date for s in stocks],
            'ticker': [s.ticker for s in stocks],
            'open': [s.open for s in stocks],
            'high': [s.high for s in stocks],
            'low': [s.low for s in stocks],
            'close': [s.close for s in stocks],
            'volume': [s.volume for s in stocks],
        }
        df = pd.DataFrame(data)
        df = df.sort_values('date')
        return df

    def _dataframe_to_stocks(
        self,
        df: pd.DataFrame,
        original_stocks: List[Stock]
    ) -> List[Stock]:
        """DataFrame을 Stock 리스트로 변환 (지표 정보 추가)"""
        # 원본 Stock 객체에 지표 정보를 딕셔너리로 저장
        result = []
        for idx, stock in enumerate(original_stocks):
            # DataFrame에서 해당 행 찾기
            row = df[
                (df['date'] == stock.date) &
                (df['ticker'] == stock.ticker)
            ]

            if not row.empty:
                # 지표 데이터를 딕셔너리로 저장
                indicators = {}
                for col in df.columns:
                    if col not in ['date', 'ticker', 'open', 'high', 'low', 'close', 'volume']:
                        indicators[col] = row[col].values[0]

                # Stock 객체의 __dict__에 indicators 추가
                stock_copy = stock
                if not hasattr(stock_copy, 'indicators'):
                    object.__setattr__(stock_copy, 'indicators', indicators)

                result.append(stock_copy)
            else:
                result.append(stock)

        return result

    def _calculate_ma(self, df: pd.DataFrame) -> pd.DataFrame:
        """이동평균선 계산"""
        for period in [5, 10, 20, 60, 120]:
            df[f'MA_{period}'] = df['close'].rolling(window=period).mean()
        return df

    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """RSI 계산"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        return df

    def _calculate_macd(
        self,
        df: pd.DataFrame,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> pd.DataFrame:
        """MACD 계산"""
        ema_fast = df['close'].ewm(span=fast).mean()
        ema_slow = df['close'].ewm(span=slow).mean()
        df['MACD'] = ema_fast - ema_slow
        df['MACD_Signal'] = df['MACD'].ewm(span=signal).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        return df

    def _calculate_bollinger_bands(
        self,
        df: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0
    ) -> pd.DataFrame:
        """볼린저 밴드 계산"""
        df['BB_Middle'] = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        df['BB_Upper'] = df['BB_Middle'] + (std * std_dev)
        df['BB_Lower'] = df['BB_Middle'] - (std * std_dev)
        return df

    def _calculate_volume_ma(self, df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """거래량 이동평균 계산"""
        df['Volume_MA'] = df['volume'].rolling(window=period).mean()
        return df
