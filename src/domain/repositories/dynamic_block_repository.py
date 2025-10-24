"""
DynamicBlockRepository Interface - 동적 블록 저장소 인터페이스

Domain layer에서 정의하는 repository interface.
Infrastructure layer에서 구현.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date

from src.domain.entities.detections import DynamicBlockDetection


class DynamicBlockRepository(ABC):
    """
    동적 블록 저장소 인터페이스

    DynamicBlockDetection 엔티티의 영속성을 담당.
    """

    @abstractmethod
    def save(self, detection: DynamicBlockDetection) -> DynamicBlockDetection:
        """
        블록 저장 (생성 또는 업데이트)

        Args:
            detection: 저장할 블록 감지 객체

        Returns:
            저장된 블록 감지 객체 (ID 할당됨)
        """
        pass

    @abstractmethod
    def save_all(self, detections: List[DynamicBlockDetection]) -> List[DynamicBlockDetection]:
        """
        여러 블록 일괄 저장

        Args:
            detections: 저장할 블록 리스트

        Returns:
            저장된 블록 리스트
        """
        pass

    @abstractmethod
    def find_by_id(self, detection_id: int) -> Optional[DynamicBlockDetection]:
        """
        ID로 블록 조회

        Args:
            detection_id: 블록 ID

        Returns:
            블록 감지 객체 또는 None
        """
        pass

    @abstractmethod
    def find_by_ticker(
        self,
        ticker: str,
        condition_name: Optional[str] = None,
        block_type: Optional[int] = None
    ) -> List[DynamicBlockDetection]:
        """
        종목 코드로 블록 조회

        Args:
            ticker: 종목 코드
            condition_name: 조건 이름 필터 (None이면 모두)
            block_type: 블록 타입 필터 (None이면 모두)

        Returns:
            블록 감지 객체 리스트
        """
        pass

    @abstractmethod
    def find_active_blocks(
        self,
        ticker: str,
        block_id: Optional[str] = None
    ) -> List[DynamicBlockDetection]:
        """
        진행 중인 블록 조회

        Args:
            ticker: 종목 코드
            block_id: 블록 ID 필터 (None이면 모두)

        Returns:
            진행 중인 블록 리스트
        """
        pass

    @abstractmethod
    def find_by_pattern_id(self, pattern_id: int) -> List[DynamicBlockDetection]:
        """
        패턴 ID로 블록 조회

        Args:
            pattern_id: 패턴 ID

        Returns:
            해당 패턴의 블록 리스트
        """
        pass

    @abstractmethod
    def find_by_date_range(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        block_type: Optional[int] = None
    ) -> List[DynamicBlockDetection]:
        """
        날짜 범위로 블록 조회

        Args:
            ticker: 종목 코드
            start_date: 시작 날짜
            end_date: 종료 날짜
            block_type: 블록 타입 필터 (None이면 모두)

        Returns:
            날짜 범위 내 블록 리스트
        """
        pass

    @abstractmethod
    def delete_by_id(self, detection_id: int) -> bool:
        """
        ID로 블록 삭제

        Args:
            detection_id: 블록 ID

        Returns:
            삭제 성공 여부
        """
        pass

    @abstractmethod
    def delete_by_ticker(self, ticker: str, condition_name: Optional[str] = None) -> int:
        """
        종목의 블록 삭제

        Args:
            ticker: 종목 코드
            condition_name: 조건 이름 필터 (None이면 모두)

        Returns:
            삭제된 블록 개수
        """
        pass
