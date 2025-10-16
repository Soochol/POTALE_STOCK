"""
Naver Finance Base Collector - 네이버 금융 데이터 수집기 베이스 클래스
"""
import time
import requests
import pandas as pd
from io import StringIO
from typing import Optional, List
from datetime import datetime
from ..base_collector import BaseCollector, CollectionResult


class NaverFinanceCollector(BaseCollector):
    """네이버 금융 데이터 수집기 베이스 클래스"""

    # 네이버 금융 기본 설정
    BASE_URL = "https://finance.naver.com"
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://finance.naver.com/'
    }

    def __init__(self, db_connection=None, delay: float = 0.2):
        """
        Args:
            db_connection: DatabaseConnection 인스턴스 (optional)
            delay: API 호출 간 대기 시간 (초) - 네이버는 0.2초 권장
        """
        super().__init__(delay)
        self.db_connection = db_connection
        self.http_session = requests.Session()
        self.http_session.headers.update(self.DEFAULT_HEADERS)

    def _fetch_html(self, url: str, params: Optional[dict] = None,
                    timeout: int = 10) -> Optional[str]:
        """
        네이버 금융에서 HTML 페이지 가져오기

        Args:
            url: 요청 URL
            params: URL 파라미터
            timeout: 타임아웃 (초)

        Returns:
            HTML 문자열 또는 None (실패 시)
        """
        try:
            response = self.http_session.get(url, params=params, timeout=timeout)
            response.raise_for_status()

            # 요청 간 딜레이
            time.sleep(self.delay)

            return response.text

        except requests.exceptions.RequestException as e:
            print(f"HTTP request failed for {url}: {e}")
            return None

    def _parse_tables(self, html: str, encoding: str = 'cp949') -> List[pd.DataFrame]:
        """
        HTML에서 테이블 추출

        Args:
            html: HTML 문자열
            encoding: 인코딩 (기본: cp949 for 한글)

        Returns:
            DataFrame 리스트
        """
        try:
            # pandas read_html을 사용하여 테이블 파싱
            dfs = pd.read_html(StringIO(html), encoding=encoding)
            return dfs

        except Exception as e:
            print(f"Failed to parse HTML tables: {e}")
            return []

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrame 정제 (공백, NaN 제거 등)

        Args:
            df: 원본 DataFrame

        Returns:
            정제된 DataFrame
        """
        # 모든 값이 NaN인 행 제거
        df = df.dropna(how='all')

        # 인덱스 리셋
        df = df.reset_index(drop=True)

        # 문자열 컬럼의 공백 제거
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.strip()
                # 'nan' 문자열을 실제 NaN으로 변환
                df[col] = df[col].replace(['nan', 'NaN', ''], pd.NA)

        return df

    def _convert_korean_number(self, value: str) -> Optional[float]:
        """
        한글 숫자 표기를 숫자로 변환
        예: "1,234", "-1,234", "1.5%" 등

        Args:
            value: 한글 숫자 문자열

        Returns:
            숫자 또는 None
        """
        if pd.isna(value) or value == '':
            return None

        try:
            # 문자열로 변환
            value = str(value).strip()

            # % 제거
            if '%' in value:
                value = value.replace('%', '')

            # 쉼표 제거
            value = value.replace(',', '')

            # 숫자로 변환
            return float(value)

        except (ValueError, AttributeError):
            return None

    def collect(self, *args, **kwargs) -> CollectionResult:
        """
        추상 메소드 구현 - 하위 클래스에서 오버라이드

        Returns:
            CollectionResult
        """
        raise NotImplementedError("Subclass must implement collect() method")
