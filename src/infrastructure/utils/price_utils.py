"""
Price Utility Functions
가격 처리 관련 유틸리티 함수
"""


def round_to_tick_size(price: float) -> int:
    """
    한국 주식 시장의 호가 단위에 맞게 가격을 반올림

    한국 주식 시장의 호가 단위는 가격대에 따라 다릅니다:
    - 1,000원 미만: 1원
    - 1,000원 ~ 5,000원 미만: 5원
    - 5,000원 ~ 10,000원 미만: 10원
    - 10,000원 ~ 50,000원 미만: 50원
    - 50,000원 ~ 100,000원 미만: 100원
    - 100,000원 ~ 500,000원 미만: 500원
    - 500,000원 이상: 1,000원

    Args:
        price: 반올림할 가격 (부동소수점)

    Returns:
        int: 호가 단위로 반올림된 정수 가격

    Examples:
        >>> round_to_tick_size(999.9)
        1000

        >>> round_to_tick_size(7339.6)  # 7,000~10,000원 구간 → 10원 단위
        7340

        >>> round_to_tick_size(52345.3)  # 50,000~100,000원 구간 → 100원 단위
        52300

        >>> round_to_tick_size(123456.7)  # 100,000~500,000원 구간 → 500원 단위
        123500

    Note:
        - fchart API에서 수정주가 계산 시 부동소수점 오차가 발생할 수 있음
        - 호가 단위로 반올림하여 데이터 정합성 보장
        - Stock 엔티티의 검증 조건 (close가 high와 low 사이) 만족
    """
    price_int = int(price)

    # 1,000원 미만: 1원 단위
    if price_int < 1000:
        return round(price)

    # 1,000원 ~ 5,000원 미만: 5원 단위
    elif price_int < 5000:
        return round(price / 5) * 5

    # 5,000원 ~ 10,000원 미만: 10원 단위
    elif price_int < 10000:
        return round(price / 10) * 10

    # 10,000원 ~ 50,000원 미만: 50원 단위
    elif price_int < 50000:
        return round(price / 50) * 50

    # 50,000원 ~ 100,000원 미만: 100원 단위
    elif price_int < 100000:
        return round(price / 100) * 100

    # 100,000원 ~ 500,000원 미만: 500원 단위
    elif price_int < 500000:
        return round(price / 500) * 500

    # 500,000원 이상: 1,000원 단위
    else:
        return round(price / 1000) * 1000
