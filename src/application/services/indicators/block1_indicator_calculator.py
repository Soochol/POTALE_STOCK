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
        ma_period: int = 20,
        exit_ma_period: Optional[int] = None,
        volume_months: Optional[Union[int, List[int]]] = 6,
        new_high_months: Optional[Union[int, List[int]]] = 2
    ) -> List[Stock]:
        """
        주식 데이터에 블록1 지표 추가

        Args:
            stocks: 주식 데이터 리스트 (동일 종목, 날짜순 정렬)
            ma_period: 진입용 이동평균선 기간
            exit_ma_period: 종료용 이동평균선 기간 (None이면 ma_period 사용)
            volume_months: 신고거래량 기간 (개월 or 개월 리스트)
            new_high_months: 신고가 기간 (개월 or 개월 리스트)

        Returns:
            지표가 추가된 주식 데이터 리스트
        """
        if not stocks:
            return []

        # Stock 리스트를 DataFrame으로 변환
        df = self._stocks_to_dataframe(stocks)

        # 지표 계산
        df = self._calculate_ma(df, ma_period)

        # 종료용 MA가 다르면 추가 계산
        if exit_ma_period and exit_ma_period != ma_period:
            df = self._calculate_ma(df, exit_ma_period)

        df = self._calculate_rate(df)
        df = self._calculate_deviation(df, ma_period)
        df = self._calculate_trading_value(df)

        # volume_months 처리 (int → [int] 변환)
        if volume_months is not None:
            volume_months_list = [volume_months] if isinstance(volume_months, int) else volume_months
            for months in volume_months_list:
                df = self._calculate_volume_high(df, months=months)

        # new_high_months 처리 (int → [int] 변환)
        if new_high_months is not None:
            new_high_months_list = [new_high_months] if isinstance(new_high_months, int) else new_high_months
            for months in new_high_months_list:
                df = self._calculate_new_high(df, months=months)

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

    def _calculate_volume_high(self, df: pd.DataFrame, months: int) -> pd.DataFrame:
        """
        N개월 최고거래량 여부 계산

        Args:
            df: DataFrame
            months: 개월 수

        Returns:
            'is_volume_high_{months}m' 컬럼이 추가된 DataFrame
        """
        # 대략적인 거래일 수 (1개월 = 20거래일)
        window = months * 20

        # 필드 이름: is_volume_high_6m, is_volume_high_12m 등
        field_name = f'is_volume_high_{months}m'
        volume_max_field = f'volume_max_{months}m'

        # 과거 N개월 최고거래량 계산 (현재 행 제외)
        # shift(1)로 자기 자신을 제외한 과거 데이터만 사용
        df[volume_max_field] = df['volume'].shift(1).rolling(window=window, min_periods=1).max()

        # 현재 거래량이 과거 최고거래량과 같거나 크면 True
        df[field_name] = (df['volume'] >= df[volume_max_field])

        return df

    def _calculate_new_high(self, df: pd.DataFrame, months: int) -> pd.DataFrame:
        """
        N개월 신고가 여부 계산 (정확한 달력 기준)

        Args:
            df: DataFrame
            months: 개월 수

        Returns:
            'is_new_high_{months}m' 컬럼이 추가된 DataFrame
        """
        # 필드 이름: is_new_high_12m, is_new_high_24m 등
        field_name = f'is_new_high_{months}m'
        df[field_name] = False

        for i in range(len(df)):
            current_date = df.loc[i, 'date']
            current_high = df.loc[i, 'high']

            # N개월 전 날짜 계산 (정확한 달력 기준)
            # relativedelta를 사용하는 대신 간단히 days로 계산
            lookback_date = current_date - timedelta(days=months * 30)

            # 과거 N개월간 최고가 찾기
            past_data = df[(df['date'] >= lookback_date) & (df['date'] < current_date)]

            if past_data.empty:
                # 과거 데이터가 없으면 신고가로 간주
                df.loc[i, field_name] = True
            else:
                # 당일 고가 >= 과거 N개월 최고가
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
