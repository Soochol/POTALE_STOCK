"""
Async Price Collector - 비동기 가격 데이터 수집기
"""
import re
import asyncio
import aiohttp
import pandas as pd
from datetime import date, datetime
from typing import List, Dict, Optional
from io import StringIO

from .base import AsyncCollectorBase
from src.infrastructure.utils import round_to_tick_size
from src.common.logging import get_logger

logger = get_logger(__name__)


class AsyncPriceCollector(AsyncCollectorBase):
    """
    비동기 가격 데이터 수집기 (OHLCV + 수정주가/거래량)

    Features:
    - fchart API에서 수정주가 수집
    - sise_day HTML에서 원본 데이터 수집
    - 수정거래량 자동 계산
    """

    # 네이버 금융 URL
    FCHART_URL = "https://fchart.stock.naver.com/siseJson.nhn"
    SISE_DAY_URL = "https://finance.naver.com/item/sise_day.nhn"

    async def collect(
        self,
        session: aiohttp.ClientSession,
        ticker: str,
        fromdate: date,
        todate: date
    ) -> Dict:
        """
        가격 데이터 수집

        Args:
            session: aiohttp 세션
            ticker: 종목 코드
            fromdate: 시작 날짜
            todate: 종료 날짜

        Returns:
            {'success': bool, 'records': List[Dict], 'error': str}
        """
        try:
            # 1. 수정주가 수집 (fchart API)
            adj_df = await self._fetch_adjusted_prices(session, ticker, fromdate, todate)

            if adj_df is None or len(adj_df) == 0:
                return {
                    'success': True,
                    'records': [],
                    'error': 'No adjusted price data'
                }

            # 2. 원본 데이터 수집 (sise_day HTML)
            raw_df = await self._fetch_raw_data(session, ticker, fromdate, todate)

            if raw_df is None or len(raw_df) == 0:
                return {
                    'success': True,
                    'records': [],
                    'error': 'No raw data'
                }

            # 3. 데이터 병합 및 수정거래량 계산
            merged_df = self._merge_and_adjust(adj_df, raw_df)

            if merged_df is None or len(merged_df) == 0:
                return {
                    'success': True,
                    'records': [],
                    'error': 'Failed to merge data'
                }

            # 4. 레코드로 변환
            records = self._to_records(merged_df, ticker)

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

    async def _fetch_adjusted_prices(
        self,
        session: aiohttp.ClientSession,
        ticker: str,
        fromdate: date,
        todate: date
    ) -> Optional[pd.DataFrame]:
        """
        fchart API에서 수정주가 비동기 수집

        Args:
            session: aiohttp 세션
            ticker: 종목 코드
            fromdate: 시작 날짜
            todate: 종료 날짜

        Returns:
            DataFrame with columns: date, adj_open, adj_high, adj_low, adj_close
        """
        params = {
            'symbol': ticker,
            'requestType': 1,
            'startTime': fromdate.strftime('%Y%m%d'),
            'endTime': todate.strftime('%Y%m%d'),
            'timeframe': 'day'
        }

        try:
            # 랜덤 헤더 + 랜덤 지연 (Rate Limiting 회피)
            await self._random_delay()
            headers = self._get_random_headers()

            async with session.get(self.FCHART_URL, params=params, headers=headers) as response:
                if response.status != 200:
                    print(f"  [Error] fchart API error for {ticker}: HTTP {response.status}")
                    return None

                text = await response.text()

                # 정규표현식으로 데이터 추출
                pattern = r'\["(\d{8})",\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\]'
                matches = re.findall(pattern, text)

                if not matches:
                    return None

                # DataFrame 생성
                data = []
                for match in matches:
                    data.append({
                        'date': pd.to_datetime(match[0], format='%Y%m%d').date(),
                        'adj_open': round_to_tick_size(float(match[1])),
                        'adj_high': round_to_tick_size(float(match[2])),
                        'adj_low': round_to_tick_size(float(match[3])),
                        'adj_close': round_to_tick_size(float(match[4])),
                    })

                df = pd.DataFrame(data)
                df = df.sort_values('date').reset_index(drop=True)

                return df

        except Exception as e:
            print(f"  [Error] Error fetching adjusted prices for {ticker}: {e}")
            return None

    async def _fetch_raw_data(
        self,
        session: aiohttp.ClientSession,
        ticker: str,
        fromdate: date,
        todate: date
    ) -> Optional[pd.DataFrame]:
        """
        sise_day HTML에서 원본 데이터 비동기 수집

        Args:
            session: aiohttp 세션
            ticker: 종목 코드
            fromdate: 시작 날짜
            todate: 종료 날짜

        Returns:
            DataFrame with columns: date, raw_close, raw_volume
        """
        all_records = []
        max_pages = 300
        page = 1

        earliest_collected = None
        pages_without_data = 0
        max_empty_pages = 10

        while page <= max_pages:
            params = {'code': ticker, 'page': page}

            try:
                # 랜덤 헤더 + 랜덤 지연 (Rate Limiting 회피)
                await self._random_delay()
                headers = self._get_random_headers()

                async with session.get(self.SISE_DAY_URL, params=params, headers=headers) as response:
                    if response.status != 200:
                        break

                    html = await response.text()

                    # pandas로 테이블 파싱 (StringIO 사용)
                    dfs = self._parse_tables(html)

                    if not dfs:
                        break

                    # 레코드 추출
                    records = self._parse_sise_day_table(dfs[0], ticker)

                    if not records:
                        pages_without_data += 1
                        if pages_without_data >= max_empty_pages:
                            break
                        page += 1
                        continue
                    else:
                        pages_without_data = 0

                    # 날짜 범위 확인
                    page_dates = [r['date'] for r in records]
                    page_earliest = min(page_dates)

                    if earliest_collected is None or page_earliest < earliest_collected:
                        earliest_collected = page_earliest

                    # 요청 범위 필터링
                    filtered = [r for r in records if fromdate <= r['date'] <= todate]
                    if filtered:
                        all_records.extend(filtered)

                    # 종료 조건
                    if page_earliest < fromdate:
                        break

                    page += 1

            except Exception as e:
                print(f"  [Error] Error at page {page} for {ticker}: {e}")
                break

        if not all_records:
            return None

        # DataFrame 변환
        df = pd.DataFrame(all_records)
        df = df.sort_values('date').reset_index(drop=True)

        return df

    def _parse_sise_day_table(
        self,
        df: pd.DataFrame,
        ticker: str
    ) -> List[Dict]:
        """
        sise_day HTML 테이블 파싱

        Args:
            df: pandas DataFrame (read_html 결과)
            ticker: 종목 코드

        Returns:
            레코드 리스트
        """
        records = []

        # DataFrame 정제
        df = self._clean_dataframe(df)

        # 날짜 컬럼 찾기
        date_col = None
        for col in df.columns:
            if '날짜' in str(col):
                date_col = col
                break

        if date_col is None:
            return records

        for _, row in df.iterrows():
            try:
                # 날짜 파싱
                date_str = str(row[date_col]).strip()
                if date_str in ['nan', 'NaN', '']:
                    continue

                # 날짜 변환
                if '.' in date_str:
                    parts = date_str.split('.')
                    if len(parts) == 3:
                        year = int(parts[0])
                        if year < 100:
                            year = 2000 + year
                        month = int(parts[1])
                        day = int(parts[2])
                        trade_date = date(year, month, day)
                    else:
                        continue
                else:
                    continue

                # 종가, 거래량 추출
                close_price = self._extract_column_value(df, row, ['종가'])
                volume = self._extract_column_value(df, row, ['거래량'])

                if close_price is None:
                    continue

                record = {
                    'date': trade_date,
                    'raw_close': int(close_price),
                    'raw_volume': int(volume) if volume is not None else 0
                }

                records.append(record)

            except Exception as e:
                # 행 파싱 실패 시 로그 남기고 계속 진행
                logger.warning(
                    "Row parsing failed in price data collection",
                    context={
                        'ticker': ticker,
                        'date_str': date_str if 'date_str' in locals() else 'unknown',
                        'row_data': str(row.to_dict()) if hasattr(row, 'to_dict') else str(row)
                    },
                    exc=e
                )
                continue

        return records

    def _merge_and_adjust(
        self,
        adj_df: pd.DataFrame,
        raw_df: pd.DataFrame
    ) -> Optional[pd.DataFrame]:
        """
        수정주가와 원본 데이터 병합 및 수정거래량 계산

        Args:
            adj_df: 수정주가 DataFrame
            raw_df: 원본 DataFrame

        Returns:
            병합된 DataFrame
        """
        try:
            # 날짜 기준 병합
            merged = pd.merge(
                adj_df,
                raw_df[['date', 'raw_close', 'raw_volume']],
                on='date',
                how='inner'
            )

            if len(merged) == 0:
                return None

            # 조정 비율 계산
            merged['price_ratio'] = merged['raw_close'] / merged['adj_close']

            # 수정거래량 계산
            def calc_adj_volume(row):
                if abs(row['price_ratio'] - 1.0) <= 0.05:
                    return row['raw_volume']
                else:
                    return int(row['raw_volume'] * row['price_ratio'])

            merged['adj_volume'] = merged.apply(calc_adj_volume, axis=1)

            # 거래대금
            merged['trading_value'] = merged['adj_close'] * merged['adj_volume']

            return merged

        except Exception as e:
            print(f"  [Error] Error merging data: {e}")
            return None

    def _to_records(self, df: pd.DataFrame, ticker: str) -> List[Dict]:
        """
        DataFrame을 DB 레코드 리스트로 변환

        Args:
            df: 병합된 DataFrame
            ticker: 종목 코드

        Returns:
            레코드 리스트
        """
        records = []

        for _, row in df.iterrows():
            record = {
                'ticker': ticker,
                'date': row['date'],
                'open': int(row['adj_open']),
                'high': int(row['adj_high']),
                'low': int(row['adj_low']),
                'close': int(row['adj_close']),
                'volume': int(row['adj_volume']),
                'trading_value': int(row['trading_value']),
                'adjustment_ratio': float(row['price_ratio']),
                'raw_close': int(row['raw_close']),
                'raw_volume': int(row['raw_volume']),
                'created_at': datetime.now()
            }
            records.append(record)

        return records
