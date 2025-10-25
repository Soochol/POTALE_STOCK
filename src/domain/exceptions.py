"""
POTALE Stock - Exception Hierarchy
도메인별 커스텀 예외 클래스

모든 POTALE_STOCK 예외의 기반이 되는 계층 구조를 정의합니다.
각 예외는 message와 context(딕셔너리)를 포함하여 디버깅을 용이하게 합니다.
"""
from typing import Dict, Any, Optional


class PotaleStockError(Exception):
    """
    Base exception for all POTALE_STOCK errors

    모든 POTALE_STOCK 예외의 최상위 클래스
    """

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        """
        Args:
            message: 에러 메시지
            context: 에러 발생 시점의 컨텍스트 정보 (딕셔너리)
        """
        self.message = message
        self.context = context or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """에러 문자열 표현"""
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} | Context: {context_str}"
        return self.message


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Domain Layer Exceptions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class DomainError(PotaleStockError):
    """
    Base for domain layer errors

    도메인 레이어에서 발생하는 모든 에러의 기반 클래스
    """
    pass


class ValidationError(DomainError):
    """
    Data validation failures

    데이터 검증 실패 (잘못된 입력, 제약조건 위반 등)
    """
    pass


class ExpressionEvaluationError(DomainError):
    """
    Expression engine evaluation failures

    표현식 엔진에서 표현식 평가 실패
    """
    pass


class BlockGraphError(DomainError):
    """
    Block graph validation/construction errors

    블록 그래프 구성 또는 검증 실패
    """
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Application Layer Exceptions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ApplicationError(PotaleStockError):
    """
    Base for application layer errors

    애플리케이션 레이어에서 발생하는 모든 에러의 기반 클래스
    """
    pass


class BlockDetectionError(ApplicationError):
    """
    Block detection failures

    블록 감지 프로세스 실패
    """
    pass


class YAMLConfigError(ApplicationError):
    """
    YAML configuration loading/parsing failures

    YAML 설정 파일 로딩 또는 파싱 실패
    """
    pass


class SeedPatternDetectionError(ApplicationError):
    """
    Seed pattern detection failures

    시드 패턴 감지 실패
    """
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Infrastructure Layer Exceptions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class InfrastructureError(PotaleStockError):
    """
    Base for infrastructure layer errors

    인프라 레이어에서 발생하는 모든 에러의 기반 클래스
    """
    pass


class DatabaseError(InfrastructureError):
    """
    Database operation failures

    데이터베이스 작업 실패 (쿼리, 연결, 트랜잭션 등)
    """
    pass


class DataCollectionError(InfrastructureError):
    """
    Data collection from external sources

    외부 소스(Naver Finance 등)에서 데이터 수집 실패
    """
    pass


class NetworkError(InfrastructureError):
    """
    Network/HTTP request failures

    네트워크 또는 HTTP 요청 실패
    """
    pass


class DataParsingError(InfrastructureError):
    """
    Data parsing/conversion failures

    데이터 파싱 또는 변환 실패 (HTML, CSV, JSON 등)
    """
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Utility Functions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def wrap_exception(
    original: Exception,
    new_exception_class: type,
    message: str,
    context: Optional[Dict[str, Any]] = None
) -> PotaleStockError:
    """
    원본 예외를 새로운 커스텀 예외로 래핑

    Args:
        original: 원본 예외
        new_exception_class: 새로운 예외 클래스
        message: 새로운 에러 메시지
        context: 추가 컨텍스트 정보

    Returns:
        래핑된 커스텀 예외

    Example:
        try:
            yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise wrap_exception(
                e, YAMLConfigError,
                "Failed to parse YAML config",
                context={"file": path}
            )
    """
    ctx = context or {}
    ctx['original_error'] = str(original)
    ctx['original_type'] = type(original).__name__

    new_exc = new_exception_class(message, context=ctx)

    # Python 3: exception chaining
    raise new_exc from original
