"""
Naver Investor Trading Collector - 네이버 금융 투자자별 거래 데이터 수집기
"""
import pandas as pd
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.dialects.sqlite import insert

from .naver_base_collector import NaverFinanceCollector, CollectionResult
from ...database.models import InvestorTrading, CollectionProgress


class NaverInvestorCollector(NaverFinanceCollector):
    """
    네이버 금융에서 개별 종목의 투자자별 거래 데이터 수집

    수집 데이터:
    - 날짜별 외국인/기관 순매수량
    - 외국인 보유주식수, 보유율
    """

    def collect(self, ticker: str, fromdate: date, todate: date) -> CollectionResult:
        """
        특정 종목의 투자자 거래 데이터 수집

        Args:
            ticker: 종목 코드 (예: "005930")
            fromdate: 시작 날짜
            todate: 종료 날짜

        Returns:
            CollectionResult
        """
        started_at = datetime.now()
        print(f"\n[Collecting] Investor trading data for {ticker} from {fromdate} to {todate}")

        try:
            # 네이버 금융 투자자별 거래 페이지
            # 이 페이지는 최근 30일 정도의 데이터를 보여줌
            url = f"{self.BASE_URL}/item/frgn.nhn"
            params = {'code': ticker}

            # HTML 가져오기
            html = self._fetch_html(url, params)
            if not html:
                return CollectionResult(
                    success=False,
                    record_count=0,
                    error_message="Failed to fetch HTML",
                    started_at=started_at,
                    completed_at=datetime.now()
                )

            # 테이블 파싱
            dfs = self._parse_tables(html)
            if len(dfs) < 4:
                return CollectionResult(
                    success=False,
                    record_count=0,
                    error_message="Investor trading table not found",
                    started_at=started_at,
                    completed_at=datetime.now()
                )

            # Table 4 (index 3)가 투자자별 거래 데이터
            df = dfs[3]

            # 데이터 정제 및 변환
            records = self._transform_dataframe(df, ticker, fromdate, todate)

            if not records:
                return CollectionResult(
                    success=True,
                    record_count=0,
                    error_message="No data in date range",
                    started_at=started_at,
                    completed_at=datetime.now()
                )

            # DB에 저장
            if self.db_connection:
                record_count = self._bulk_upsert(records)
                self._update_progress(ticker, fromdate, todate, record_count, success=True)
            else:
                record_count = len(records)

            completed_at = datetime.now()
            print(f"[Success] Collected {record_count} records for {ticker}")

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
        네이버 금융 DataFrame을 InvestorTrading 레코드로 변환

        네이버 컬럼 구조:
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
            print("[Warning] Date column not found in DataFrame")
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
                print(f"[Warning] Failed to parse row {idx}: {e}")
                continue

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
            stmt = insert(InvestorTrading).values(records)
            stmt = stmt.on_conflict_do_update(
                index_elements=['ticker', 'date'],
                set_={
                    'institution_net_buy': stmt.excluded.institution_net_buy,
                    'foreign_net_buy': stmt.excluded.foreign_net_buy,
                    'individual_net_buy': stmt.excluded.individual_net_buy,
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
            collection_type = f"investor_trading_{ticker}"

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
