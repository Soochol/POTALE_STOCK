"""
Common Data Converters
Repository에서 사용하는 공통 변환 함수들
"""


def bool_to_int(value: bool) -> int:
    """
    Boolean을 Integer로 변환 (DB 저장용)

    Args:
        value: Boolean 값

    Returns:
        1 (True) 또는 0 (False)
    """
    return 1 if value else 0


def int_to_bool(value: int) -> bool:
    """
    Integer를 Boolean으로 변환 (DB에서 로드)

    Args:
        value: Integer 값 (0 또는 1)

    Returns:
        True (1) 또는 False (0)
    """
    return value == 1
