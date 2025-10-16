"""
Naver Stock Price Collector - 네이버 금융 주가 데이터 수집기
"""
import pandas as pd
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.dialects.sqlite import insert

from .naver_base_collector import NaverFinanceCollector, CollectionResult
from ...database.models import StockPrice, CollectionProgress


class NaverPriceCollector(NaverFinanceCollector):
    """
    네이버 금융에서 개별 종목의 일별 주가 데이터 수집

    수집 데이터:
    - 날짜별 시가/고가/저가/종가
    - 거래량
    - 거래대금
    """

    def collect(self, ticker: str, fromdate: date, todate: date) -> CollectionResult:
        """
        특정 종목의 주가 데이터 수집

        Args:
            ticker: 종목 코드 (예: "005930")
            fromdate: 시작 날짜
            todate: 종료 날짜

        Returns:
            CollectionResult
        """
        started_at = datetime.now()
        print(f"\n[Collecting] Stock price data for {ticker} from {fromdate} to {todate}")

        try:
            all_records = []

            # 네이버 금융 일별 시세 페이지는 페이지네이션 필요
            # 한 페이지당 10일치 데이터 제공
            page = 1
            max_pages = 500  # 최대 5,000일치 (약 13년)

            while page <= max_pages:
                url = f"{self.BASE_URL}/item/sise_day.nhn"
                params = {'code': ticker, 'page': page}

                # HTML 가져오기
                html = self._fetch_html(url, params)
                if not html:
                    print(f"[Warning] Failed to fetch page {page}")
                    break

                # 테이블 파싱
                dfs = self._parse_tables(html)
                if not dfs or len(dfs) == 0:
                    print(f"[Warning] No tables found on page {page}")
                    break

                # 첫 번째 테이블이 주가 데이터
                df = dfs[0]

                # 데이터 정제 및 변환
                records = self._transform_dataframe(df, ticker, fromdate, todate)

                if not records:
                    # 더 이상 데이터가 없거나 날짜 범위를 벗어남
                    break

                all_records.extend(records)

                # fromdate보다 오래된 데이터가 나오면 중단
                earliest_date = min(r['date'] for r in records)
                if earliest_date < fromdate:
                    # fromdate 이후 데이터만 필터링
                    all_records = [r for r in all_records if r['date'] >= fromdate]
                    break

                page += 1

            if not all_records:
                return CollectionResult(
                    success=True,
                    record_count=0,
                    error_message="No data in date range",
                    started_at=started_at,
                    completed_at=datetime.now()
                )

            # DB에 저장
            if self.db_connection:
                record_count = self._bulk_upsert(all_records)
                self._update_progress(ticker, fromdate, todate, record_count, success=True)
            else:
                record_count = len(all_records)

            completed_at = datetime.now()
            print(f"[Success] Collected {record_count} records for {ticker} ({page} pages)")

            return CollectionResult(
                success=True,
                record_count=record_count,
                started_at=started_at,
                completed_at=completed_at
            )

        except Exception as e:
            completed_at = datetime.now()
            error_msg = f"Error collecting data for {ticker}: {str(e)}"
            print(f"[Error] {error_msg}")

            if self.db_connection:
                self._update_progress(ticker, fromdate, todate, 0, success=False, error_msg=error_msg)

            return CollectionResult(
                success=False,
                record_count=0,
                error_message=error_msg,
                started_at=started_at,
                completed_at=completed_at
            )

    def _transform_dataframe(self, df: pd.DataFrame, ticker: str,
                            fromdate: date, todate: date) -> List[Dict]:
        """
        네이버 금융 DataFrame을 StockPrice 레코드로 변환

        네이버 컬럼 구조:
        - 날짜
        - 종가
        - 전일비
        - 시가
        - 고가
        - 저가
        - 거래량

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

        # 컬럼명 확인
        expected_cols = ['날짜', '종가', '시가', '고가', '저가', '거래량']

        # 날짜 컬럼 찾기
        date_col = None
        for col in df.columns:
            if '날짜' in str(col):
                date_col = col
                break

        if date_col is None:
            print("[Warning] Date column not found in DataFrame")
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
                    'volume': int(volume) if volume is not None else 0,
                    'created_at': datetime.now()
                }

                records.append(record)

            except Exception as e:
                print(f"[Warning] Failed to parse row {idx}: {e}")
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

    def _update_progress(self, ticker: str, fromdate: date, todate: date,
                        record_count: int, success: bool = True,
                        error_msg: Optional[str] = None):
        """
        수집 진행 상황 업데이트

        Args:
            ticker: 종목 코드
            fromdate: 시작 날짜
            todate: 종료 날짜
            record_count: 수집된 레코드 수
            success: 성공 여부
            error_msg: 에러 메시지 (실패 시)
        """
        if not self.db_connection:
            return

        session = self.db_connection.get_session()

        try:
            # CollectionProgress 레코드 생성/업데이트
            collection_type = f"stock_price_{ticker}"

            # 기존 레코드 찾기
            progress = session.query(CollectionProgress).filter_by(
                collection_type=collection_type,
                target_date=fromdate
            ).first()

            if progress:
                # 업데이트
                progress.status = 'completed' if success else 'failed'
                progress.record_count = record_count
                progress.completed_at = datetime.now()
                if error_msg:
                    progress.error_message = error_msg
                    progress.retry_count += 1
            else:
                # 새로 생성
                progress = CollectionProgress(
                    collection_type=collection_type,
                    target_date=fromdate,
                    status='completed' if success else 'failed',
                    record_count=record_count,
                    started_at=datetime.now(),
                    completed_at=datetime.now(),
                    error_message=error_msg,
                    retry_count=1 if not success else 0
                )
                session.add(progress)

            session.commit()

        except Exception as e:
            session.rollback()
            print(f"[Warning] Failed to update collection progress: {e}")
        finally:
            session.close()
