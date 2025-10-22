"""
Block1 Indicator Calculator - 블록1 전용 지표 계산 서비스
"""
from src.domain.entities import Stock
from typing import List, Dict, Optional, Union
from datetime import date, timedelta
import pandas as pd
from src.application.services.three_line_break import ThreeLineBreakCalculator

class Block1IndicatorCalculator:
    """
    블록1 탐지를 위한 기술적 지표 계산 서비스

    계산하는 지표:
    - 이동평균선 (MA)
    - 등락률 (전일 대비)
    - 이격도 (이동평균선 기준)
    - N개월 최고거래량
    - 삼선전환도
    """

    def __init__(self):
        self.tlb_calculator = ThreeLineBreakCalculator(line_count=3)

    def calculate(
        self,
        stocks: List[Stock],
        ma_period: Optional[int] = None,
        ma_periods: Optional[List[int]] = None,
        exit_ma_period: Optional[int] = None,
        volume_days: Optional[Union[int, List[int]]] = None,
        new_high_days: Optional[Union[int, List[int]]] = None
    ) -> List[Stock]:
        """
        주식 데이터에 블록1 지표 추가

        Args:
            stocks: 주식 데이터 리스트 (동일 종목, 날짜순 정렬)
            ma_period: 진입용 이동평균선 기간 (단일 값)
            ma_periods: 이동평균선 기간 리스트 (여러 값, ma_period보다 우선)
            exit_ma_period: 종료용 이동평균선 기간 (None이면 ma_period 사용)
            volume_days: 신고거래량 기간 (달력 기준 일수 or 일수 리스트)
            new_high_days: 신고가 기간 (달력 기준 일수 or 일수 리스트)

        Returns:
            지표가 추가된 주식 데이터 리스트
        """
        if not stocks:
            return []

        # Stock 리스트를 DataFrame으로 변환
        df = self._stocks_to_dataframe(stocks)

        # MA period 처리 (ma_periods가 우선, 없으면 ma_period 사용)
        if ma_periods:
            periods_to_calculate = ma_periods
        elif ma_period:
            periods_to_calculate = [ma_period]
        else:
            periods_to_calculate = [20]  # 기본값

        # 모든 MA period 계산
        for period in periods_to_calculate:
            df = self._calculate_ma(df, period)

        # 종료용 MA 추가 계산
        if exit_ma_period and exit_ma_period not in periods_to_calculate:
            df = self._calculate_ma(df, exit_ma_period)

        # 기본 MA period 설정 (deviation 계산용)
        primary_ma_period = periods_to_calculate[0] if periods_to_calculate else 20

        df = self._calculate_rate(df)
        df = self._calculate_deviation(df, primary_ma_period)
        df = self._calculate_trading_value(df)

        # volume_days 처리 (int → [int] 변환)
        if volume_days is not None:
            volume_days_list = [volume_days] if isinstance(volume_days, int) else volume_days
            for days in volume_days_list:
                df = self._calculate_volume_high(df, days=days)

        # new_high_days 처리 (int → [int] 변환)
        if new_high_days is not None:
            new_high_days_list = [new_high_days] if isinstance(new_high_days, int) else new_high_days
            for days in new_high_days_list:
                df = self._calculate_new_high(df, days=days)

        # 삼선전환도 계산
        tlb_bars = self.tlb_calculator.calculate(
            dates=df['date'].tolist(),
            opens=df['open'].tolist(),
            highs=df['high'].tolist(),
            lows=df['low'].tolist(),
            closes=df['close'].tolist()
        )

        # DataFrame에 삼선전환도 정보 추가
        tlb_dict = {bar.date: bar for bar in tlb_bars}
        df['tlb_direction'] = df['date'].apply(
            lambda d: tlb_dict[d].direction if d in tlb_dict else None
        )

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
        df = df.sort_values('date').reset_index(drop=True)
        return df

    def _dataframe_to_stocks(
        self,
        df: pd.DataFrame,
        original_stocks: List[Stock]
    ) -> List[Stock]:
        """DataFrame을 Stock 리스트로 변환 (지표 정보 추가)"""
        result = []
        for stock in original_stocks:
            # DataFrame에서 해당 행 찾기
            row = df[df['date'] == stock.date]

            if not row.empty:
                # 지표 데이터를 딕셔너리로 저장
                indicators = {}
                for col in df.columns:
                    if col not in ['date', 'ticker', 'open', 'high', 'low', 'close', 'volume']:
                        val = row[col].values[0]
                        # NaN 처리
                        if pd.notna(val):
                            indicators[col] = val

                # Stock 객체에 indicators 추가
                if not hasattr(stock, 'indicators'):
                    object.__setattr__(stock, 'indicators', indicators)
                else:
                    # 기존 indicators 업데이트
                    stock.indicators.update(indicators)

                result.append(stock)
            else:
                result.append(stock)

        return result

    def _calculate_ma(self, df: pd.DataFrame, period: int) -> pd.DataFrame:
        """이동평균선 계산"""
        col_name = f'MA_{period}'
        df[col_name] = df['close'].rolling(window=period, min_periods=1).mean()
        return df

    def _calculate_rate(self, df: pd.DataFrame) -> pd.DataFrame:
        """등락률 계산 (고가 기준, 전일종가 대비 %)"""
        df['prev_close'] = df['close'].shift(1)
        df['rate'] = ((df['high'] - df['prev_close']) / df['prev_close'] * 100).fillna(0)
        return df

    def _calculate_deviation(self, df: pd.DataFrame, ma_period: int) -> pd.DataFrame:
        """이격도 계산 (MA를 100으로 봤을 때 종가 비율)"""
        ma_col = f'MA_{ma_period}'
        if ma_col not in df.columns:
            df = self._calculate_ma(df, ma_period)

        # 이격도 = (종가 / MA) * 100
        # MA를 100으로 봤을 때 종가가 몇인지
        df['deviation'] = (df['close'] / df[ma_col] * 100).fillna(100)
        return df

    def _calculate_trading_value(self, df: pd.DataFrame) -> pd.DataFrame:
        """거래대금 계산 (억 단위)"""
        df['trading_value_100m'] = (df['close'] * df['volume']) / 100_000_000
        return df

    def _calculate_volume_high(self, df: pd.DataFrame, days: int) -> pd.DataFrame:
        """
        N일 최고거래량 여부 계산 (달력 기준)

        Args:
            df: DataFrame
            days: 달력 기준 일수 (예: 90일, 180일, 365일)

        Returns:
            'is_volume_high_{days}d' 컬럼이 추가된 DataFrame
        """
        # 필드 이름: is_volume_high_90d, is_volume_high_180d 등
        field_name = f'is_volume_high_{days}d'
        volume_max_field = f'volume_max_{days}d'

        df[field_name] = False
        df[volume_max_field] = None

        # 각 행에 대해 과거 N일간 최고거래량 계산 (정확한 달력 기준)
        for i in range(len(df)):
            current_date = df.loc[i, 'date']
            current_volume = df.loc[i, 'volume']

            # N일 전 날짜 계산 (정확한 달력 기준)
            lookback_date = current_date - timedelta(days=days)

            # 과거 N일간 거래량 찾기 (자기 자신 제외)
            past_data = df[(df['date'] >= lookback_date) & (df['date'] < current_date)]

            if past_data.empty:
                # 과거 데이터가 없으면 신고거래량으로 간주
                df.loc[i, field_name] = True
                df.loc[i, volume_max_field] = current_volume
            else:
                # 당일 거래량 >= 과거 N일 최고거래량
                past_max_volume = past_data['volume'].max()
                df.loc[i, volume_max_field] = past_max_volume
                df.loc[i, field_name] = (current_volume >= past_max_volume)

        return df

    def _calculate_new_high(self, df: pd.DataFrame, days: int) -> pd.DataFrame:
        """
        N일 신고가 여부 계산 (정확한 달력 기준)

        Args:
            df: DataFrame
            days: 달력 기준 일수 (예: 90일, 180일, 365일)

        Returns:
            'is_new_high_{days}d' 컬럼이 추가된 DataFrame
        """
        # 필드 이름: is_new_high_90d, is_new_high_180d 등
        field_name = f'is_new_high_{days}d'
        df[field_name] = False

        for i in range(len(df)):
            current_date = df.loc[i, 'date']
            current_high = df.loc[i, 'high']

            # N일 전 날짜 계산 (정확한 달력 기준)
            lookback_date = current_date - timedelta(days=days)

            # 과거 N일간 최고가 찾기
            past_data = df[(df['date'] >= lookback_date) & (df['date'] < current_date)]

            if past_data.empty:
                # 과거 데이터가 없으면 신고가로 간주
                df.loc[i, field_name] = True
            else:
                # 당일 고가 >= 과거 N일 최고가
                past_max_high = past_data['high'].max()
                df.loc[i, field_name] = (current_high >= past_max_high)

        return df

    def get_three_line_break_bars(self, stocks: List[Stock]):
        """
        삼선전환도 바 리스트 반환

        Args:
            stocks: 주식 데이터 리스트

        Returns:
            ThreeLineBreakBar 리스트
        """
        if not stocks:
            return []

        df = self._stocks_to_dataframe(stocks)

        return self.tlb_calculator.calculate(
            dates=df['date'].tolist(),
            opens=df['open'].tolist(),
            highs=df['high'].tolist(),
            lows=df['low'].tolist(),
            closes=df['close'].tolist()
        )
