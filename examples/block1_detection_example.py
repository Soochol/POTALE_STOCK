"""
블록1 탐지 시스템 사용 예제

이 파일은 블록1 탐지 시스템을 사용하는 방법을 보여줍니다.
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import date, timedelta
from src.domain.entities.stock import Stock
from src.domain.entities.block1_condition import Block1Condition, Block1ExitConditionType
from src.application.use_cases.detect_block1 import DetectBlock1UseCase
from src.infrastructure.repositories.block1_repository import Block1Repository
from src.infrastructure.database.connection import DatabaseConnection


def example_1_basic_detection():
    """기본 블록1 탐지 예제"""
    print("=" * 80)
    print("예제 1: 기본 블록1 탐지")
    print("=" * 80)

    # 1. 블록1 조건 정의
    condition = Block1Condition(
        rate_threshold=5.0,           # 등락률 5% 이상
        ma_period=20,                  # 20일 이동평균선
        high_above_ma=True,            # 고가 >= 20일선
        deviation_threshold=10.0,      # 이격도 10% 이하
        trading_value_threshold=100.0, # 거래대금 100억 이상
        volume_months=6,               # 6개월 신고거래량
        exit_condition_type=Block1ExitConditionType.MA_BREAK,  # 이평선 이탈로 종료
        cooldown_days=120              # 120일 중복 방지
    )

    # 2. 데이터베이스 연결
    db = DatabaseConnection("stock_data.db")

    # 3. Repository 생성
    repository = Block1Repository(db)

    # 4. Use Case 생성
    use_case = DetectBlock1UseCase(repository)

    # 5. 주식 데이터 준비 (예시 - 실제로는 DB에서 조회)
    stocks = [
        Stock(
            ticker="005930",
            date=date(2024, 1, 2),
            open=70000,
            high=72000,
            low=69500,
            close=71500,
            volume=10000000
        ),
        # ... 더 많은 데이터
    ]

    # 6. 블록1 탐지 실행
    detections = use_case.execute(
        condition=condition,
        condition_name="기본_블록1",
        stocks=stocks
    )

    # 7. 결과 출력
    print(f"\n탐지된 블록1: {len(detections)}개")
    for detection in detections:
        print(f"  - {detection.ticker}: {detection.started_at} (상태: {detection.status})")


def example_2_three_line_reversal():
    """삼선전환도 종료 조건 예제"""
    print("\n" + "=" * 80)
    print("예제 2: 삼선전환도 첫 음봉으로 종료")
    print("=" * 80)

    condition = Block1Condition(
        rate_threshold=3.0,
        ma_period=5,
        high_above_ma=True,
        trading_value_threshold=50.0,
        exit_condition_type=Block1ExitConditionType.THREE_LINE_REVERSAL,  # 삼선전환도
        cooldown_days=60
    )

    print(f"종료 조건: {condition.exit_condition_type.value}")


def example_3_body_middle_exit():
    """캔들 몸통 중간 가격 이탈 종료 예제"""
    print("\n" + "=" * 80)
    print("예제 3: 블록1 캔들 몸통 중간 가격 이탈로 종료")
    print("=" * 80)

    condition = Block1Condition(
        rate_threshold=7.0,
        ma_period=10,
        deviation_threshold=15.0,
        volume_months=3,
        exit_condition_type=Block1ExitConditionType.BODY_MIDDLE,  # 몸통 중간 이탈
        cooldown_days=90
    )

    print(f"종료 조건: {condition.exit_condition_type.value}")


def example_4_query_blocks():
    """블록1 조회 예제"""
    print("\n" + "=" * 80)
    print("예제 4: 블록1 조회")
    print("=" * 80)

    db = DatabaseConnection("stock_data.db")
    repository = Block1Repository(db)
    use_case = DetectBlock1UseCase(repository)

    # 활성 블록1 조회
    active_blocks = use_case.get_active_blocks("005930")
    print(f"\n삼성전자 활성 블록1: {len(active_blocks)}개")

    # 특정 기간 블록1 조회
    all_blocks = use_case.get_all_blocks(
        ticker="005930",
        from_date=date(2024, 1, 1),
        to_date=date(2024, 12, 31)
    )
    print(f"2024년 삼성전자 전체 블록1: {len(all_blocks)}개")

    # 블록1 상세 정보 출력
    for block in all_blocks[:5]:  # 최대 5개만
        print(f"\n블록1 ID: {block.block1_id}")
        print(f"  시작일: {block.started_at}")
        print(f"  진입가: {block.entry_close:,}원")
        print(f"  진입 거래량: {block.entry_volume:,}주")
        print(f"  상태: {block.status}")
        if block.status == "completed":
            print(f"  종료일: {block.ended_at}")
            print(f"  종료 사유: {block.exit_reason}")
            print(f"  지속 기간: {block.duration_days}일")


def example_5_custom_conditions():
    """다양한 조건 조합 예제"""
    print("\n" + "=" * 80)
    print("예제 5: 다양한 조건 조합")
    print("=" * 80)

    # 조건 1: 급등주 (등락률 + 거래대금 중심)
    condition_surge = Block1Condition(
        rate_threshold=10.0,           # 10% 이상 상승
        trading_value_threshold=200.0, # 200억 이상
        volume_months=3,               # 3개월 신고거래량
        cooldown_days=30               # 30일 중복 방지
    )
    print("\n조건 1 (급등주):", condition_surge)

    # 조건 2: 이평선 돌파 (이평선 중심)
    condition_ma_break = Block1Condition(
        rate_threshold=3.0,
        ma_period=60,                  # 60일선
        high_above_ma=True,
        deviation_threshold=5.0,       # 이격도 5% 이하
        exit_condition_type=Block1ExitConditionType.MA_BREAK
    )
    print("조건 2 (이평선 돌파):", condition_ma_break)

    # 조건 3: 거래량 중심
    condition_volume = Block1Condition(
        volume_months=12,              # 12개월 신고거래량
        trading_value_threshold=300.0, # 300억 이상
        cooldown_days=180              # 180일 중복 방지
    )
    print("조건 3 (거래량 중심):", condition_volume)


def main():
    """메인 함수"""
    print("\n블록1 탐지 시스템 사용 예제\n")

    # 예제 실행
    # example_1_basic_detection()  # 실제 DB 필요
    example_2_three_line_reversal()
    example_3_body_middle_exit()
    # example_4_query_blocks()  # 실제 DB 필요
    example_5_custom_conditions()

    print("\n" + "=" * 80)
    print("예제 실행 완료")
    print("=" * 80)


if __name__ == "__main__":
    main()
