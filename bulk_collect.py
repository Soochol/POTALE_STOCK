#!/usr/bin/env python
"""
대규모 주식 데이터 수집 CLI

사용법:
    # 전체 종목 수집 (수정주가 + 수정거래량)
    python bulk_collect.py --all --from 2020-01-01 --to 2024-12-31

    # 특정 종목들만 수집
    python bulk_collect.py --tickers 005930,000660 --from 2024-01-01

    # 이어서 수집 (중단된 지점부터)
    python bulk_collect.py --all --from 2020-01-01 --resume

    # 투자자 정보도 함께 수집
    python bulk_collect.py --all --from 2024-01-01 --investor

    # 레거시 모드 (원본 주가만)
    python bulk_collect.py --all --from 2024-01-01 --legacy
"""

import argparse
import sys
from datetime import date, datetime
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.infrastructure.database.connection import DatabaseConnection
from src.infrastructure.collectors.bulk_collector import BulkCollector
from src.infrastructure.utils.naver_ticker_list import get_all_tickers as get_naver_tickers


def parse_date(date_str: str) -> date:
    """날짜 문자열을 date 객체로 변환"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")


def get_all_tickers() -> list[str]:
    """네이버 금융을 사용하여 전체 종목 코드 가져오기"""
    try:
        return get_naver_tickers()
    except Exception as e:
        print(f"[Error] 종목 리스트 로딩 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="대규모 주식 데이터 수집 (하이브리드 모드: 수정주가 + 수정거래량)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # 종목 선택
    ticker_group = parser.add_mutually_exclusive_group(required=True)
    ticker_group.add_argument(
        "--all",
        action="store_true",
        help="전체 종목 수집 (KOSPI + KOSDAQ, ~2,500종목)"
    )
    ticker_group.add_argument(
        "--tickers",
        type=str,
        help="특정 종목 코드들 (쉼표로 구분, 예: 005930,000660,035720)"
    )

    # 날짜 범위
    parser.add_argument(
        "--from",
        dest="fromdate",
        type=parse_date,
        required=True,
        help="시작 날짜 (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--to",
        dest="todate",
        type=parse_date,
        default=date.today(),
        help="종료 날짜 (YYYY-MM-DD, 기본값: 오늘)"
    )

    # 수집 옵션
    parser.add_argument(
        "--investor",
        action="store_true",
        help="투자자별 거래 정보도 수집"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="중단된 지점부터 이어서 수집"
    )
    parser.add_argument(
        "--legacy",
        action="store_true",
        help="레거시 모드 (원본 주가만, 하이브리드 비활성화)"
    )

    # 성능 옵션
    parser.add_argument(
        "--delay",
        type=float,
        default=0.2,
        help="API 요청 간 대기 시간 (초, 기본값: 0.2)"
    )
    parser.add_argument(
        "--db",
        type=str,
        default="data/database/stock_data.db",
        help="데이터베이스 파일 경로 (기본값: data/database/stock_data.db)"
    )

    args = parser.parse_args()

    # 종목 리스트 결정
    if args.all:
        tickers = get_all_tickers()
    else:
        tickers = [t.strip() for t in args.tickers.split(",")]
        print(f"수집 대상 종목: {len(tickers)}개")

    # 설정 출력
    print("\n" + "=" * 80)
    print("대규모 주식 데이터 수집 시작")
    print("=" * 80)
    print(f"종목 수: {len(tickers):,}개")
    print(f"기간: {args.fromdate} ~ {args.todate}")
    print(f"수집 방식: {'레거시 (원본 주가)' if args.legacy else '하이브리드 (수정주가+수정거래량)'}")
    print(f"투자자 정보: {'수집' if args.investor else '미수집'}")
    print(f"이어하기: {'활성화' if args.resume else '비활성화'}")
    print(f"API 대기 시간: {args.delay}초")
    print(f"DB: {args.db}")
    print("=" * 80)

    # 사용자 확인
    if len(tickers) > 100:
        response = input(f"\n{len(tickers):,}개 종목을 수집하시겠습니까? (y/N): ")
        if response.lower() != 'y':
            print("수집 취소됨")
            sys.exit(0)

    # 데이터베이스 연결
    print(f"\nDB 연결 중: {args.db}")
    db = DatabaseConnection(args.db)
    db.create_tables()
    print("DB 테이블 생성 완료")

    # BulkCollector 초기화
    collector = BulkCollector(
        db_connection=db,
        delay=args.delay,
        use_hybrid=not args.legacy  # legacy 모드가 아니면 하이브리드 사용
    )

    # 수집 실행
    try:
        stats = collector.collect_all_stocks(
            tickers=tickers,
            fromdate=args.fromdate,
            todate=args.todate,
            collect_price=True,
            collect_investor=args.investor,
            resume=args.resume
        )

        # 최종 통계 출력
        elapsed_seconds = (stats.completed_at - stats.started_at).total_seconds()

        print("\n" + "=" * 80)
        print("수집 완료!")
        print("=" * 80)
        print(f"총 종목: {stats.total_tickers:,}개")
        print(f"성공: {stats.completed_tickers:,}개")
        print(f"실패: {stats.failed_tickers:,}개")
        print(f"레코드: {stats.total_records:,}개")
        print(f"소요 시간: {elapsed_seconds:.1f}초 ({elapsed_seconds/3600:.2f}시간)")
        if elapsed_seconds > 0:
            print(f"평균 속도: {stats.total_records/elapsed_seconds:.1f} rec/s")
        print("=" * 80)

    except KeyboardInterrupt:
        print("\n\n수집 중단됨 (Ctrl+C)")
        print("다음에 --resume 옵션으로 이어서 수집할 수 있습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[Error] 수집 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
