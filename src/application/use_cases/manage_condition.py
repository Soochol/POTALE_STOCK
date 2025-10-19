"""
Manage Condition Use Cases - 조건 관리 유스케이스들
"""
from typing import List, Optional
from src.domain.entities.condition import Condition, Rule
from src.domain.repositories.condition_repository import IConditionRepository


class CreateConditionUseCase:
    """조건 생성 유스케이스"""

    def __init__(self, condition_repository: IConditionRepository):
        self.condition_repository = condition_repository

    def execute(
        self,
        name: str,
        description: str,
        rules: List[Rule]
    ) -> Condition:
        """
        조건 생성 실행

        Args:
            name: 조건 이름
            description: 조건 설명
            rules: 규칙 리스트

        Returns:
            생성된 조건 객체
        """
        # 중복 확인
        if self.condition_repository.exists(name):
            raise ValueError(f"이미 존재하는 조건입니다: {name}")

        # 조건 생성
        condition = Condition(
            name=name,
            description=description,
            rules=rules
        )

        # 유효성 검사
        if not condition.validate():
            raise ValueError("유효하지 않은 조건입니다")

        # 저장
        success = self.condition_repository.save(condition)
        if not success:
            raise RuntimeError("조건 저장에 실패했습니다")

        return condition


class UpdateConditionUseCase:
    """조건 수정 유스케이스"""

    def __init__(self, condition_repository: IConditionRepository):
        self.condition_repository = condition_repository

    def execute(
        self,
        name: str,
        description: Optional[str] = None,
        rules: Optional[List[Rule]] = None
    ) -> Condition:
        """
        조건 수정 실행

        Args:
            name: 조건 이름
            description: 새로운 설명 (선택)
            rules: 새로운 규칙 리스트 (선택)

        Returns:
            수정된 조건 객체
        """
        # 기존 조건 조회
        condition = self.condition_repository.get_by_name(name)
        if not condition:
            raise ValueError(f"조건을 찾을 수 없습니다: {name}")

        # 수정
        if description is not None:
            condition.description = description
        if rules is not None:
            condition.rules = rules

        # 유효성 검사
        if not condition.validate():
            raise ValueError("유효하지 않은 조건입니다")

        # 저장
        success = self.condition_repository.update(condition)
        if not success:
            raise RuntimeError("조건 수정에 실패했습니다")

        return condition


class DeleteConditionUseCase:
    """조건 삭제 유스케이스"""

    def __init__(self, condition_repository: IConditionRepository):
        self.condition_repository = condition_repository

    def execute(self, name: str) -> bool:
        """
        조건 삭제 실행

        Args:
            name: 조건 이름

        Returns:
            성공 여부
        """
        # 존재 확인
        if not self.condition_repository.exists(name):
            raise ValueError(f"조건을 찾을 수 없습니다: {name}")

        # 삭제
        success = self.condition_repository.delete(name)
        if not success:
            raise RuntimeError("조건 삭제에 실패했습니다")

        return True


class ListConditionsUseCase:
    """조건 목록 조회 유스케이스"""

    def __init__(self, condition_repository: IConditionRepository):
        self.condition_repository = condition_repository

    def execute(self) -> List[Condition]:
        """
        모든 조건 조회

        Returns:
            조건 리스트
        """
        return self.condition_repository.get_all()
