"""
Query Builder for Detection Repositories
명시적이고 체이닝 가능한 쿼리 빌더
"""
from typing import List, Optional, Type, TypeVar, Generic
from datetime import date
from sqlalchemy.orm import Session, Query

ModelType = TypeVar('ModelType')


class DetectionQueryBuilder(Generic[ModelType]):
    """
    블록 탐지 결과 쿼리 빌더

    복잡한 쿼리를 명시적이고 체이닝 가능한 방식으로 작성합니다.
    AI가 이해하고 생성하기 쉬운 패턴을 제공합니다.

    Example:
        >>> builder = DetectionQueryBuilder(session, Block1DetectionModel)
        >>> results = builder.by_ticker("005930") \\
        ...                  .by_status("active") \\
        ...                  .between_dates(start_date, end_date) \\
        ...                  .order_by_started_date() \\
        ...                  .all()
    """

    def __init__(self, session: Session, model_class: Type[ModelType]):
        """
        쿼리 빌더 초기화

        Args:
            session: SQLAlchemy 세션
            model_class: 모델 클래스 (Block1DetectionModel 등)
        """
        self.session = session
        self.model_class = model_class
        self._query: Query = session.query(model_class)

    def by_ticker(self, ticker: str) -> 'DetectionQueryBuilder[ModelType]':
        """
        종목코드로 필터링

        Args:
            ticker: 종목코드

        Returns:
            Self for chaining
        """
        self._query = self._query.filter(self.model_class.ticker == ticker)
        return self

    def by_status(self, status: str) -> 'DetectionQueryBuilder[ModelType]':
        """
        상태로 필터링

        Args:
            status: 상태 ("active", "completed")

        Returns:
            Self for chaining
        """
        self._query = self._query.filter(self.model_class.status == status)
        return self

    def by_active(self) -> 'DetectionQueryBuilder[ModelType]':
        """
        활성 상태만 필터링

        Returns:
            Self for chaining
        """
        return self.by_status("active")

    def by_completed(self) -> 'DetectionQueryBuilder[ModelType]':
        """
        완료 상태만 필터링

        Returns:
            Self for chaining
        """
        return self.by_status("completed")

    def between_dates(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> 'DetectionQueryBuilder[ModelType]':
        """
        시작일 범위로 필터링

        Args:
            from_date: 시작일 (이상)
            to_date: 종료일 (이하)

        Returns:
            Self for chaining
        """
        if from_date:
            self._query = self._query.filter(self.model_class.started_at >= from_date)
        if to_date:
            self._query = self._query.filter(self.model_class.started_at <= to_date)
        return self

    def after_date(self, after: date) -> 'DetectionQueryBuilder[ModelType]':
        """
        특정 날짜 이후만 필터링

        Args:
            after: 기준 날짜

        Returns:
            Self for chaining
        """
        self._query = self._query.filter(self.model_class.started_at > after)
        return self

    def before_date(self, before: date) -> 'DetectionQueryBuilder[ModelType]':
        """
        특정 날짜 이전만 필터링

        Args:
            before: 기준 날짜

        Returns:
            Self for chaining
        """
        self._query = self._query.filter(self.model_class.started_at < before)
        return self

    def order_by_started_date(self, desc: bool = False) -> 'DetectionQueryBuilder[ModelType]':
        """
        시작일로 정렬

        Args:
            desc: True면 내림차순, False면 오름차순

        Returns:
            Self for chaining
        """
        if desc:
            self._query = self._query.order_by(self.model_class.started_at.desc())
        else:
            self._query = self._query.order_by(self.model_class.started_at)
        return self

    def limit(self, count: int) -> 'DetectionQueryBuilder[ModelType]':
        """
        결과 개수 제한

        Args:
            count: 최대 개수

        Returns:
            Self for chaining
        """
        self._query = self._query.limit(count)
        return self

    def all(self) -> List[ModelType]:
        """
        모든 결과 조회

        Returns:
            List[ModelType]: 결과 리스트
        """
        return self._query.all()

    def first(self) -> Optional[ModelType]:
        """
        첫 번째 결과 조회

        Returns:
            Optional[ModelType]: 첫 번째 결과 또는 None
        """
        return self._query.first()

    def count(self) -> int:
        """
        결과 개수 조회

        Returns:
            int: 결과 개수
        """
        return self._query.count()

    def exists(self) -> bool:
        """
        결과 존재 여부 확인

        Returns:
            bool: 결과가 1개 이상이면 True
        """
        return self.count() > 0
