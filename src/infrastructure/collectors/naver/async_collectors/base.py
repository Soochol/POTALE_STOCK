"""
Async Collector Base - 비동기 수집기 베이스 클래스
"""
import random
import asyncio
import pandas as pd
from io import StringIO
from typing import Optional, List
from datetime import datetime


class AsyncCollectorBase:
    """비동기 수집기 공통 기능 베이스 클래스"""

    # 네이버 금융 기본 설정
    BASE_URL = "https://finance.naver.com"

    # User-Agent 회전 (7가지 변형)
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]

    # Referer 회전 (3가지 변형)
    REFERERS = [
        'https://finance.naver.com/',
        'https://finance.naver.com/sise/',
        'https://finance.naver.com/item/main.naver',
    ]

    def __init__(self, delay: float = 0.1):
        """
        Args:
            delay: 요청 간 기본 대기 시간 (초)
        """
        self.delay = delay

    def _get_random_headers(self) -> dict:
        """
        랜덤 HTTP 헤더 생성 (User-Agent + Referer 회전)

        Returns:
            HTTP 헤더 딕셔너리
        """
        return {
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': random.choice(self.REFERERS),
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    async def _random_delay(self):
        """
        랜덤 지연 (delay ± 50%)

        봇 탐지 회피를 위해 요청 간 지연 시간을 무작위로 변경
        """
        min_delay = self.delay * 0.5
        max_delay = self.delay * 1.5
        actual_delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(actual_delay)

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
            # StringIO로 감싸서 FutureWarning 방지
            dfs = pd.read_html(StringIO(html), encoding=encoding)
            return dfs
        except Exception as e:
            print(f"[Warning] Failed to parse HTML tables: {e}")
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

    def _convert_korean_number(self, value) -> Optional[float]:
        """
        한글 숫자 표기를 숫자로 변환
        예: "1,234", "-1,234", "1.5%" 등

        Args:
            value: 한글 숫자 문자열 또는 숫자

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
