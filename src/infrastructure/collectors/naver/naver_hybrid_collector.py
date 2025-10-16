"""
Naver Hybrid Collector
수정주가(fchart API) + 원본데이터(sise_day) 하이브리드 수집기

수정주가와 수정거래량을 모두 제공하기 위한 하이브리드 방식:
1. fchart API에서 수정주가 수집
2. sise_day에서 원본 주가/거래량 수집
3. 두 데이터를 비교하여 조정 비율 계산
4. 조정 비율을 거래량에 적용하여 수정거래량 생성
"""
import re
import requests
import pandas as pd
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional
from time import sleep
from sqlalchemy.dialects.sqlite import insert

from .naver_base_collector import NaverFinanceCollector, CollectionResult
from ...database.models import StockPrice


class NaverHybridCollector(NaverFinanceCollector):
    """
    네이버 하이브리드 데이터 수집기

    Features:
    - fchart API로 수정주가 수집
    - sise_day HTML로 원본 데이터 수집
    - 자동으로 수정거래량 계산
    """

    FCHART_URL = "https://fchart.stock.naver.com/siseJson.nhn"

    def __init__(self, db_connection=None, delay: float = 0.1):
        """
        Args:
            db_connection: DB 연결 (선택)
            delay: 요청 간 지연 시간 (초)
        """
        super().__init__(db_connection, delay)

    def collect(self, ticker: str, fromdate: date, todate: date) -> CollectionResult:
        """
        주식 데이터 수집 (수정주가 + 수정거래량)

        Args:
            ticker: 종목코드
            fromdate: 시작일
            todate: 종료일

        Returns:
            CollectionResult
        """
        started_at = datetime.now()
        print(f"\n[Hybrid Collecting] {ticker} ({fromdate} ~ {todate})")

        try:
            # 1. fchart API에서 수정주가 수집
            adj_df = self._fetch_adjusted_prices(ticker, fromdate, todate)

            if adj_df is None or len(adj_df) == 0:
                return CollectionResult(
                    success=True,
                    record_count=0,
                    error_message="No adjusted price data",
                    started_at=started_at,
                    completed_at=datetime.now()
                )

            # 2. sise_day에서 원본 데이터 수집
            raw_df = self._fetch_raw_data(ticker, fromdate, todate)

            if raw_df is None or len(raw_df) == 0:
                return CollectionResult(
                    success=True,
                    record_count=0,
                    error_message="No raw data",
                    started_at=started_at,
                    completed_at=datetime.now()
                )

            # 3. 데이터 병합 및 수정거래량 계산
            merged_df = self._merge_and_adjust(adj_df, raw_df)

            if merged_df is None or len(merged_df) == 0:
                return CollectionResult(
                    success=True,
                    record_count=0,
                    error_message="Failed to merge data",
                    started_at=started_at,
                    completed_at=datetime.now()
                )

            # 4. 딕셔너리 리스트로 변환
            records = self._to_records(merged_df, ticker)

            # 5. DB에 저장
            if self.db_connection:
                record_count = self._bulk_upsert(records)
            else:
                record_count = len(records)

            completed_at = datetime.now()
            print(f"[Success] Collected {record_count} hybrid records for {ticker}")

            return CollectionResult(
                success=True,
                record_count=record_count,
                started_at=started_at,
                completed_at=completed_at
            )

        except Exception as e:
            completed_at = datetime.now()
            error_msg = f"Error collecting hybrid data for {ticker}: {str(e)}"
            print(f"[Error] {error_msg}")

            return CollectionResult(
                success=False,
                record_count=0,
                error_message=error_msg,
                started_at=started_at,
                completed_at=completed_at
            )

    def _fetch_adjusted_prices(self, ticker: str, fromdate: date, todate: date) -> Optional[pd.DataFrame]:
        """
        fchart API에서 수정주가 가져오기

        Returns:
            DataFrame with columns: date, adj_open, adj_high, adj_low, adj_close
        """
        params = {
            'symbol': ticker,
            'requestType': 1,  # 수정주가 요청
            'startTime': fromdate.strftime('%Y%m%d'),
            'endTime': todate.strftime('%Y%m%d'),
            'timeframe': 'day'
        }

        try:
            response = self.http_session.get(
                self.FCHART_URL,
                params=params,
                timeout=10
            )

            if response.status_code != 200:
                print(f"[Error] fchart API error: HTTP {response.status_code}")
                return None

            # 정규표현식으로 데이터 추출
            # 형식: ["20180402", 6960, 7180, 6790, 6810, 136356, 36.68]
            pattern = r'\["(\d{8})",\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\]'
            matches = re.findall(pattern, response.text)

            if not matches:
                print(f"[Error] No data found in fchart response for {ticker}")
                return None

            # DataFrame 생성
            data = []
            for match in matches:
                data.append({
                    'date': pd.to_datetime(match[0], format='%Y%m%d').date(),
                    'adj_open': int(match[1]),
                    'adj_high': int(match[2]),
                    'adj_low': int(match[3]),
                    'adj_close': int(match[4]),
                    # fchart의 거래량은 사용하지 않음 (sise_day에서 가져온 raw_volume 사용)
                    # 'fchart_volume': int(match[5]),  # 참고: fchart API의 거래량은 부정확함
                })

            df = pd.DataFrame(data)
            df = df.sort_values('date').reset_index(drop=True)

            print(f"    fchart: {len(df)} adjusted price records")

            return df

        except Exception as e:
            print(f"[Error] Error fetching adjusted prices: {e}")
            return None

    def _fetch_raw_data(self, ticker: str, fromdate: date, todate: date) -> Optional[pd.DataFrame]:
        """
        sise_day HTML에서 원본 데이터 가져오기

        Returns:
            DataFrame with columns: date, raw_open, raw_high, raw_low, raw_close, raw_volume
        """
        all_records = []
        max_pages = 300  # 충분한 페이지 수

        # 목표 날짜까지 페이지 추정
        days_since_start = (date.today() - fromdate).days

        # 최근 1년 이내 데이터면 페이지 1부터 시작
        if days_since_start < 365:
            page = 1
        else:
            # 오래된 데이터는 추정 페이지부터 시작
            estimated_start_page = max(1, days_since_start // 10)
            page = max(1, estimated_start_page - 20)

        print(f"    Starting from page {page} (days_since_start: {days_since_start})")

        while page <= max_pages:
            params = {'code': ticker, 'page': page}

            try:
                url = f"{self.BASE_URL}/item/sise_day.nhn"
                html = self._fetch_html(url, params)

                if not html:
                    break

                dfs = self._parse_tables(html)

                if not dfs:
                    break

                records = self._transform_dataframe(dfs[0], ticker, fromdate, todate)

                if not records:
                    # 날짜 범위 벗어남
                    if all_records:  # 이미 데이터가 있으면 중단
                        break
                    else:  # 아직 도달 안 함
                        page += 1
                        continue

                all_records.extend(records)

                # fromdate보다 오래된 데이터가 나오면 중단
                earliest_date = min(r['date'] for r in records)
                if earliest_date < fromdate:
                    all_records = [r for r in all_records if r['date'] >= fromdate]
                    break

                page += 1

                # 진행상황 로깅
                if page % 50 == 0:
                    print(f"    Checked {page} pages for {ticker}...")

                sleep(self.delay)

            except Exception as e:
                print(f"[Error] Error at page {page}: {e}")
                break

        if not all_records:
            print(f"[Error] No raw data collected for {ticker}")
            return None

        # DataFrame 변환
        df = pd.DataFrame(all_records)
        df = df.sort_values('date').reset_index(drop=True)

        # 컬럼명 변경
        df = df.rename(columns={
            'open': 'raw_open',
            'high': 'raw_high',
            'low': 'raw_low',
            'close': 'raw_close',
            'volume': 'raw_volume'
        })

        print(f"    sise_day: {len(df)} raw data records from {page} pages")

        return df

    def _merge_and_adjust(self, adj_df: pd.DataFrame, raw_df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        수정주가 데이터와 원본 데이터를 병합하고 수정거래량 계산

        Args:
            adj_df: 수정주가 데이터
            raw_df: 원본 데이터

        Returns:
            병합된 DataFrame with adjusted volumes
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
                print("[Error] No matching dates between adjusted and raw data")
                return None

            # 조정 비율 계산
            merged['price_ratio'] = merged['raw_close'] / merged['adj_close']

            # 수정거래량 계산
            def calculate_adjusted_volume(row):
                price_ratio = row['price_ratio']

                # 가격이 일치하면 조정 불필요 (액면분할 이후)
                if abs(price_ratio - 1.0) <= 0.05:
                    return row['raw_volume']
                else:
                    # 가격 비율만큼 거래량 조정 (액면분할 이전)
                    return int(row['raw_volume'] * price_ratio)

            merged['adj_volume'] = merged.apply(calculate_adjusted_volume, axis=1)

            # 거래대금 계산
            merged['trading_value'] = merged['adj_close'] * merged['adj_volume']

            # 조정 통계 로깅
            adjusted_count = sum(abs(merged['price_ratio'] - 1.0) > 0.05)
            if adjusted_count > 0:
                print(f"    Applied volume adjustment to {adjusted_count} rows "
                      f"(price_ratio != 1.0)")

            return merged

        except Exception as e:
            print(f"[Error] Error merging data: {e}")
            return None

    def _to_records(self, df: pd.DataFrame, ticker: str) -> List[Dict]:
        """
        DataFrame을 딕셔너리 리스트로 변환

        Args:
            df: 병합된 DataFrame
            ticker: 종목코드

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

                # 참고용 추가 정보
                'adjustment_ratio': float(row['price_ratio']),
                'raw_close': int(row['raw_close']),
                'raw_volume': int(row['raw_volume']),

                # 생성 시각
                'created_at': datetime.now()
            }

            records.append(record)

        return records

    def _bulk_upsert(self, records: List[Dict]) -> int:
        """
        대량 upsert (INSERT OR REPLACE)

        Args:
            records: 레코드 리스트

        Returns:
            저장된 레코드 수
        """
        if not records:
            return 0

        session = self.db_connection.get_session()

        try:
            # SQLite의 INSERT OR REPLACE 사용
            stmt = insert(StockPrice).values(records)
            stmt = stmt.on_conflict_do_update(
                index_elements=['ticker', 'date'],
                set_={
                    'open': stmt.excluded.open,
                    'high': stmt.excluded.high,
                    'low': stmt.excluded.low,
                    'close': stmt.excluded.close,
                    'volume': stmt.excluded.volume,
                    'trading_value': stmt.excluded.trading_value,
                    'adjustment_ratio': stmt.excluded.adjustment_ratio,
                    'raw_close': stmt.excluded.raw_close,
                    'raw_volume': stmt.excluded.raw_volume,
                    'created_at': stmt.excluded.created_at
                }
            )

            session.execute(stmt)
            session.commit()

            return len(records)

        except Exception as e:
            session.rollback()
            print(f"[Error] Bulk upsert failed: {e}")
            raise
        finally:
            session.close()

    def _transform_dataframe(self, df: pd.DataFrame, ticker: str,
                            fromdate: date, todate: date) -> List[Dict]:
        """
        네이버 금융 DataFrame을 레코드로 변환 (원본 데이터용)

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

        # 날짜 컬럼 찾기
        date_col = None
        for col in df.columns:
            if '날짜' in str(col):
                date_col = col
                break

        if date_col is None:
            return records

        # 각 행 처리
        for idx, row in df.iterrows():
            try:
                # 날짜 파싱
                date_str = str(row[date_col]).strip()
                if date_str in ['nan', 'NaN', '']:
                    continue

                # 날짜 변환 (형식: "2024.10.16")
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

                # 날짜 범위 체크
                if trade_date < fromdate or trade_date > todate:
                    continue

                # 가격 데이터 추출
                close_price = self._extract_column_value(df, row, ['종가'])
                open_price = self._extract_column_value(df, row, ['시가'])
                high_price = self._extract_column_value(df, row, ['고가'])
                low_price = self._extract_column_value(df, row, ['저가'])
                volume = self._extract_column_value(df, row, ['거래량'])

                # 필수 필드 검증
                if close_price is None:
                    continue

                record = {
                    'ticker': ticker,
                    'date': trade_date,
                    'open': int(open_price) if open_price is not None else None,
                    'high': int(high_price) if high_price is not None else None,
                    'low': int(low_price) if low_price is not None else None,
                    'close': int(close_price),
                    'volume': int(volume) if volume is not None else 0
                }

                records.append(record)

            except Exception as e:
                # Silent skip
                continue

        return records

    def _extract_column_value(self, df: pd.DataFrame, row: pd.Series,
                             col_keywords: List[str]) -> Optional[float]:
        """
        DataFrame에서 특정 키워드를 포함한 컬럼의 값 추출

        Args:
            df: DataFrame
            row: 현재 행
            col_keywords: 찾을 컬럼 키워드 리스트

        Returns:
            숫자 값 또는 None
        """
        for keyword in col_keywords:
            for col in df.columns:
                if keyword in str(col):
                    value = row[col]
                    if not pd.isna(value):
                        return self._convert_korean_number(value)
        return None
