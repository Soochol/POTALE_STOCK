"""
아난티 데이터 수집 및 블록1 탐지 (2015-2025)
"""
import sys
from pathlib import Path
from datetime import date

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.infrastructure.collectors.naver.naver_hybrid_collector import NaverHybridCollector
from src.infrastructure.database.connection import DatabaseConnection
from src.infrastructure.database.models import Base, StockInfo
from src.infrastructure.repositories.sqlite_stock_repository import SqliteStockRepository
from src.infrastructure.repositories.block1_repository import Block1Repository
from src.application.use_cases.detect_block1 import DetectBlock1UseCase
from src.domain.entities.block1_condition import Block1Condition, Block1ExitConditionType


def main():
    print("=" * 80)
    print("아난티 데이터 수집 및 블록1 탐지 (2015-2025)")
    print("=" * 80)

    # 1. DB 초기화
    db_path = "stock_data.db"
    db = DatabaseConnection(db_path)
    Base.metadata.create_all(db.engine)
    print(f"Database initialized: {db_path}\n")

    # 2. StockInfo 확인/추가
    session = db.get_session()
    ticker = "025980"
    stock_info = session.query(StockInfo).filter(StockInfo.ticker == ticker).first()
    if not stock_info:
        stock_info = StockInfo(ticker=ticker, name="아난티", market="KOSDAQ")
        session.add(stock_info)
        session.commit()
        print(f"StockInfo added: {ticker} (아난티)\n")
    session.close()

    # 3. 데이터 수집
    collector = NaverHybridCollector(db_connection=db)
    stock_repo = SqliteStockRepository(db_path)

    fromdate = date(2015, 1, 1)
    todate = date(2025, 12, 31)  # 2025년까지

    print(f"[수집 시작] {ticker} ({fromdate} ~ {todate})")
    result = collector.collect(ticker, fromdate, todate)

    if not result.success:
        print(f"[Error] 데이터 수집 실패: {result.error_message}")
        return

    print(f"[성공] {result.record_count}건 수집 완료 ({result.duration_seconds:.1f}초)\n")

    # 4. 데이터 로드
    stocks = stock_repo.get_stock_data(ticker, fromdate, todate)
    if len(stocks) == 0:
        print("[Error] 수집된 데이터가 DB에서 조회되지 않습니다.")
        return

    print(f"[DATA] 데이터 로드: {len(stocks)}개 레코드")
    print(f"기간: {stocks[0].date} ~ {stocks[-1].date}\n")

    # 5. 블록1 조건 설정 (새로운 엄격한 조건)
    condition = Block1Condition(
        rate_threshold=8.0,                     # 고가 기준 등락률 8% 이상 (전일종가 대비)
        ma_period=120,                          # 진입: 120일 이동평균선
        high_above_ma=True,                     # 고가 >= MA120
        deviation_threshold=120.0,              # 이격도 120 이하 (MA를 100으로 봤을 때)
        trading_value_threshold=300.0,          # 거래대금 300억원 이상
        volume_months=24,                       # 24개월(2년) 신고거래량
        prev_day_volume_increase_ratio=400,     # 전날 거래량 대비 400% (4배, 필수)
        new_high_months=2,                      # 2개월 신고가 (필수)
        exit_condition_type=Block1ExitConditionType.MA_BREAK,
        exit_ma_period=60,                      # 종료: 종가 < MA60
        cooldown_days=120
    )

    print(f"블록1 조건: {condition}\n")

    # 6. 블록1 탐지
    block1_repo = Block1Repository(db)

    # 기존 Block1 확인
    existing_detections = block1_repo.find_by_ticker(ticker)
    print(f"기존 Block1: {len(existing_detections)}개\n")

    if len(existing_detections) > 0:
        print("기존 Block1이 있습니다. 기존 데이터를 출력합니다.")
        print("(새로 탐지하려면 DB의 block1_detection 테이블을 삭제하세요)\n")
        detections = existing_detections
    else:
        use_case = DetectBlock1UseCase(block1_repo)
        print("블록1 탐지 실행 중...\n")
        detections = use_case.execute(
            condition=condition,
            condition_name="아난티_2015-2025",
            stocks=stocks
        )

    # 7. 결과 출력
    print("=" * 80)
    print(f"블록1 탐지 결과: {len(detections)}개 발견")
    print("=" * 80)

    if not detections:
        print("\n탐지된 블록1이 없습니다.")
        return

    # 연도별 통계
    by_year = {}
    for d in detections:
        year = d.started_at.year
        if year not in by_year:
            by_year[year] = []
        by_year[year].append(d)

    print(f"\n연도별 블록1 분포:")
    for year in sorted(by_year.keys()):
        count = len(by_year[year])
        gains = [d.peak_gain_ratio for d in by_year[year] if d.peak_gain_ratio]
        if gains:
            avg_gain = sum(gains) / len(gains)
            print(f"  {year}년: {count}개 (평균 상승률: {avg_gain:.2f}%)")
        else:
            print(f"  {year}년: {count}개")

    # 상위 출력
    print(f"\n" + "=" * 80)
    print("블록1 목록 (최고가 상승률 순)")
    print("=" * 80)

    sorted_detections = sorted(detections,
                               key=lambda d: d.peak_gain_ratio if d.peak_gain_ratio else 0,
                               reverse=True)

    for i, detection in enumerate(sorted_detections, 1):
        status_text = "진행중" if detection.status == "active" else "완료"
        print(f"\n[{i}] {detection.started_at} ~ {detection.ended_at or '진행중'} ({status_text})")

        print(f"    진입가: {detection.entry_close:,.0f}원")
        if detection.entry_rate:
            print(f"    등락률: {detection.entry_rate:.2f}%")

        if detection.peak_price:
            print(f"    최고가: {detection.peak_price:,.0f}원 ({detection.peak_date})")
            if detection.peak_gain_ratio:
                print(f"    상승률: {detection.peak_gain_ratio:.2f}%")

        if detection.status == "completed" and detection.duration_days:
            print(f"    지속: {detection.duration_days}일, 종료: {detection.exit_reason}")

    # 8. 전체 통계
    print(f"\n" + "=" * 80)
    print("전체 통계")
    print("=" * 80)

    active = [d for d in detections if d.status == "active"]
    completed = [d for d in detections if d.status == "completed"]

    print(f"활성 블록1: {len(active)}개")
    print(f"완료 블록1: {len(completed)}개")

    if completed:
        avg_duration = sum(d.duration_days for d in completed if d.duration_days) / len(completed)
        gains = [d.peak_gain_ratio for d in completed if d.peak_gain_ratio]
        if gains:
            avg_gain = sum(gains) / len(gains)
            max_gain = max(gains)
            min_gain = min(gains)

            print(f"\n완료 블록1 평균 통계:")
            print(f"  평균 지속 기간: {avg_duration:.1f}일")
            print(f"  평균 최고가 상승률: {avg_gain:.2f}%")
            print(f"  최대 상승률: {max_gain:.2f}%")
            print(f"  최소 상승률: {min_gain:.2f}%")

    print("=" * 80)


if __name__ == "__main__":
    main()
