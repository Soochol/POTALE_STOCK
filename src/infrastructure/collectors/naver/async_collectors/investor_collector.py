"""
Async Investor Collector - 비동기 투자자별 거래 데이터 수집기
"""
import asyncio
import aiohttp
import pandas as pd
from datetime import date, datetime
from typing import List, Dict, Optional

from .base import AsyncCollectorBase


class AsyncInvestorCollector(AsyncCollectorBase):
    """
    비동기 투자자별 거래 데이터 수집기

    Features:
    - 기관/외국인 순매수량 수집
    - User-Agent 회전으로 Rate Limiting 회피
    """

    # 네이버 금융 투자자 거래 URL
    INVESTOR_URL = "https://finance.naver.com/item/frgn.nhn"

    async def collect(
        self,
        session: aiohttp.ClientSession,
        ticker: str,
        fromdate: date,
        todate: date
    ) -> Dict:
        """
        투자자 거래 데이터 수집

        Args:
            session: aiohttp 세션
            ticker: 종목 코드
            fromdate: 시작 날짜
            todate: 종료 날짜

        Returns:
            {'success': bool, 'records': List[Dict], 'error': str}
        """
        try:
            params = {'code': ticker}

            # 랜덤 헤더 + 랜덤 지연 (Rate Limiting 회피)
            await self._random_delay()
            headers = self._get_random_headers()

            async with session.get(self.INVESTOR_URL, params=params, headers=headers) as response:
                if response.status != 200:
                    return {
                        'success': False,
                        'records': [],
                        'error': f'HTTP {response.status}'
                    }

                html = await response.text()

            # 테이블 파싱
            dfs = self._parse_tables(html)
            if len(dfs) < 4:
                return {
                    'success': False,
                    'records': [],
                    'error': 'Investor trading table not found'
                }

            # Table 4 (index 3)가 투자자별 거래 데이터
            df = dfs[3]

            # 데이터 정제 및 변환
            records = self._parse_investor_data(df, ticker, fromdate, todate)

            if not records:
                return {
                    'success': True,
                    'records': [],
                    'error': 'No data in date range'
                }

            return {
                'success': True,
                'records': records,
                'error': None
            }

        except Exception as e:
            return {
                'success': False,
                'records': [],
                'error': str(e)
            }

    def _parse_investor_data(
        self,
        df: pd.DataFrame,
        ticker: str,
        fromdate: date,
        todate: date
    ) -> List[Dict]:
        """
        네이버 금융 DataFrame을 InvestorTrading 레코드로 변환

        네이버 컬럼 구조 (MultiIndex):
        - ('날짜', '날짜')
        - ('종가', '종가')
        - ('전일비', '전일비')
        - ('등락률', '등락률')
        - ('거래량', '거래량')
        - ('기관', '순매수량')
        - ('외국인', '순매수량')
        - ('외국인', '보유주식수')
        - ('외국인', '보유율')

        Args:
            df: 네이버에서 파싱한 DataFrame
            ticker: 종목 코드
            fromdate: 시작 날짜
            todate: 종료 날짜

        Returns:
            레코드 리스트
        """
        records = []

        # DataFrame 정제
        df = self._clean_dataframe(df)

        # 컬럼명이 MultiIndex인 경우 처리
        if isinstance(df.columns, pd.MultiIndex):
            # 첫 번째 레벨을 사용하되, 중복은 두 번째 레벨과 결합
            new_cols = []
            for col in df.columns:
                if col[0] == col[1]:
                    new_cols.append(col[0])
                else:
                    new_cols.append(f"{col[0]}_{col[1]}")
            df.columns = new_cols

        # 날짜 컬럼 찾기
        date_col = None
        for col in df.columns:
            if '날짜' in str(col):
                date_col = col
                break

        if date_col is None:
            print(f"  [Warning] Date column not found in DataFrame for {ticker}")
            return records

        # 각 행 처리
        for idx, row in df.iterrows():
            try:
                # 날짜 파싱
                date_str = str(row[date_col]).strip()
                if date_str in ['nan', 'NaN', '']:
                    continue

                # 날짜 변환 (형식: "24.09.20" 또는 "2024.09.20")
                if '.' in date_str:
                    parts = date_str.split('.')
                    if len(parts) == 3:
                        year = int(parts[0])
                        # 2자리 연도를 4자리로 변환
                        if year < 100:
                            year = 2000 + year
                        month = int(parts[1])
                        day = int(parts[2])
                        trade_date = date(year, month, day)
                    else:
                        continue
                else:
                    continue

                # 날짜 범위 체크
                if trade_date < fromdate or trade_date > todate:
                    continue

                # 기관 순매수량 (단위: 주)
                institution_net = None
                for col in df.columns:
                    col_str = str(col)
                    # MultiIndex: ('기관', '순매수량') 형태
                    if '기관' in col_str and ('순매수' in col_str or col_str.count('기관') > 0):
                        value = row[col]
                        if not pd.isna(value):
                            institution_net = self._convert_korean_number(value)
                            if institution_net is not None:
                                break

                # 외국인 순매수량 (단위: 주)
                foreign_net = None
                for col in df.columns:
                    col_str = str(col)
                    # MultiIndex: ('외국인', '순매수량') 형태, 단 보유주식수/보유율이 아닌 것
                    if '외국인' in col_str and ('순매수' in col_str or '보유' not in col_str):
                        value = row[col]
                        if not pd.isna(value) and '보유' not in col_str:
                            # '순매수량' 컬럼이 먼저 나오므로 첫 번째 외국인 컬럼이 순매수량
                            potential_value = self._convert_korean_number(value)
                            if potential_value is not None and abs(potential_value) < 1e12:  # 보유주식수는 매우 큰 값
                                foreign_net = potential_value
                                break

                # 개인 순매수는 네이버에서 직접 제공하지 않음
                # (개인 = - (기관 + 외국인))으로 계산 가능하지만, 일단 0으로 설정

                record = {
                    'ticker': ticker,
                    'date': trade_date,
                    'institution_net_buy': int(institution_net) if institution_net is not None else 0,
                    'foreign_net_buy': int(foreign_net) if foreign_net is not None else 0,
                    'individual_net_buy': 0,  # 네이버는 개인 데이터 미제공
                    'created_at': datetime.now()
                }

                records.append(record)

            except Exception as e:
                print(f"  [Warning] Failed to parse row {idx} for {ticker}: {e}")
                continue

        return records
