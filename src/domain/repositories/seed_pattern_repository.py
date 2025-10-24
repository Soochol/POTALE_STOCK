"""
Seed Pattern Repository Interface

Seed pattern 영속성 인터페이스 (Domain Layer)
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date

from src.domain.entities.patterns import SeedPattern, SeedPatternStatus


class SeedPatternRepository(ABC):
    """
    Seed Pattern Repository 인터페이스

    Seed detection 결과를 저장하고 조회하는 저장소
    """

    @abstractmethod
    def save(self, seed_pattern: SeedPattern) -> SeedPattern:
        """
        Seed pattern 저장 (생성 또는 업데이트)

        Args:
            seed_pattern: 저장할 seed pattern

        Returns:
            저장된 seed pattern (ID 포함)
        """
        pass

    @abstractmethod
    def save_all(self, seed_patterns: List[SeedPattern]) -> List[SeedPattern]:
        """
        여러 seed pattern 일괄 저장

        Args:
            seed_patterns: 저장할 seed pattern 리스트

        Returns:
            저장된 seed pattern 리스트 (ID 포함)
        """
        pass

    @abstractmethod
    def find_by_id(self, seed_pattern_id: int) -> Optional[SeedPattern]:
        """
        ID로 seed pattern 조회

        Args:
            seed_pattern_id: Seed pattern ID

        Returns:
            SeedPattern 또는 None
        """
        pass

    @abstractmethod
    def find_by_name(self, pattern_name: str) -> Optional[SeedPattern]:
        """
        이름으로 seed pattern 조회

        Args:
            pattern_name: 패턴 이름

        Returns:
            SeedPattern 또는 None
        """
        pass

    @abstractmethod
    def find_by_ticker(
        self,
        ticker: str,
        status: Optional[SeedPatternStatus] = None
    ) -> List[SeedPattern]:
        """
        종목 코드로 seed pattern 조회

        Args:
            ticker: 종목 코드
            status: 상태 필터 (None이면 전체)

        Returns:
            SeedPattern 리스트
        """
        pass

    @abstractmethod
    def find_active_patterns(self, ticker: Optional[str] = None) -> List[SeedPattern]:
        """
        활성화된 seed pattern 조회

        Args:
            ticker: 종목 코드 (None이면 전체)

        Returns:
            활성 상태의 SeedPattern 리스트
        """
        pass

    @abstractmethod
    def find_by_date_range(
        self,
        start_date: date,
        end_date: date,
        ticker: Optional[str] = None
    ) -> List[SeedPattern]:
        """
        날짜 범위로 seed pattern 조회

        Args:
            start_date: 시작 날짜
            end_date: 종료 날짜
            ticker: 종목 코드 (None이면 전체)

        Returns:
            SeedPattern 리스트
        """
        pass

    @abstractmethod
    def find_all(
        self,
        status: Optional[SeedPatternStatus] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[SeedPattern]:
        """
        모든 seed pattern 조회 (페이지네이션)

        Args:
            status: 상태 필터 (None이면 전체)
            limit: 최대 개수 (None이면 전체)
            offset: 시작 위치

        Returns:
            SeedPattern 리스트
        """
        pass

    @abstractmethod
    def count(
        self,
        ticker: Optional[str] = None,
        status: Optional[SeedPatternStatus] = None
    ) -> int:
        """
        Seed pattern 개수 조회

        Args:
            ticker: 종목 코드 (None이면 전체)
            status: 상태 필터 (None이면 전체)

        Returns:
            개수
        """
        pass

    @abstractmethod
    def delete_by_id(self, seed_pattern_id: int) -> bool:
        """
        ID로 seed pattern 삭제

        Args:
            seed_pattern_id: Seed pattern ID

        Returns:
            삭제 성공 여부
        """
        pass

    @abstractmethod
    def delete_by_ticker(self, ticker: str) -> int:
        """
        종목의 모든 seed pattern 삭제

        Args:
            ticker: 종목 코드

        Returns:
            삭제된 개수
        """
        pass

    @abstractmethod
    def update_status(
        self,
        seed_pattern_id: int,
        status: SeedPatternStatus
    ) -> bool:
        """
        Seed pattern 상태 업데이트

        Args:
            seed_pattern_id: Seed pattern ID
            status: 새 상태

        Returns:
            업데이트 성공 여부
        """
        pass
