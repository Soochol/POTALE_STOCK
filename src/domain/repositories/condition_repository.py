"""
Condition Repository Interface - 조건 저장소 인터페이스
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.condition import Condition


class IConditionRepository(ABC):
    """조건 저장소 인터페이스"""

    @abstractmethod
    def get_all(self) -> List[Condition]:
        """
        모든 조건 조회

        Returns:
            조건 리스트
        """
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Condition]:
        """
        이름으로 조건 조회

        Args:
            name: 조건 이름

        Returns:
            조건 객체 또는 None
        """
        pass

    @abstractmethod
    def save(self, condition: Condition) -> bool:
        """
        조건 저장

        Args:
            condition: 조건 객체

        Returns:
            성공 여부
        """
        pass

    @abstractmethod
    def update(self, condition: Condition) -> bool:
        """
        조건 수정

        Args:
            condition: 조건 객체

        Returns:
            성공 여부
        """
        pass

    @abstractmethod
    def delete(self, name: str) -> bool:
        """
        조건 삭제

        Args:
            name: 조건 이름

        Returns:
            성공 여부
        """
        pass

    @abstractmethod
    def exists(self, name: str) -> bool:
        """
        조건 존재 여부 확인

        Args:
            name: 조건 이름

        Returns:
            존재 여부
        """
        pass
