"""
단일 종목 데이터 수집 스크립트

2015-01-01부터 현재까지 1개 종목의 주가 및 투자자 데이터를 수집합니다.

Features:
- AsyncUnifiedCollector 활용한 고성능 비동기 수집
- 증분 수집 지원 (이미 수집된 데이터는 건너뛰기)
- 주가 데이터 + 투자자 데이터 동시 수집
- Rich 라이브러리로 진행 상황 시각화
- 데이터베이스 자동 초기화

Usage:
    # 아난티(025980) 수집
    uv run python scripts/collect_single_ticker.py --ticker 025980

    # 삼성전자(005930) 수집
    uv run python scripts/collect_single_ticker.py --ticker 005930

    # 투자자 데이터 제외 (주가만)
    uv run python scripts/collect_single_ticker.py --ticker 025980 --no-investor

    # 전체 재수집 (증분 무시)
    uv run python scripts/collect_single_ticker.py --ticker 025980 --force-full
"""
import argparse
import asyncio
import os
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

# Constants
DEFAULT_FROM_DATE = "2015-01-01"
DEFAULT_DB_PATH = "data/database/stock_data.db"
API_DELAY = 0.1
MAX_RETRIES = 3
SEPARATOR_WIDTH = 80

# Windows 콘솔 UTF-8 설정
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.collectors.incremental_collector import IncrementalCollector
from src.infrastructure.collectors.naver.async_unified_collector import (
    AsyncUnifiedCollector,
)
from src.infrastructure.database.connection import get_db_connection

console = Console()


def create_stats_table(result, ticker: str, fromdate: date, todate: date, elapsed_seconds: float) -> Table:
    """
    수집 결과 통계 테이블 생성

    Args:
        result: 수집 결과 객체
        ticker: 종목 코드
        fromdate: 수집 시작일
        todate: 수집 종료일
        elapsed_seconds: 소요 시간(초)

    Returns:
        Table: 수집 통계가 담긴 Rich Table 객체
    """
    table = Table(title=f"수집 결과 - {ticker}", show_header=True, header_style="bold cyan")
    table.add_column("항목", style="cyan", width=20)
    table.add_column("값", style="green", width=40)

    table.add_row("종목 코드", ticker)
    table.add_row("수집 기간", f"{fromdate} ~ {todate}")
    table.add_row("성공 여부", "성공" if result.success else "실패")
    table.add_row("주가 데이터", f"{result.price_record_count:,}건")
    table.add_row("투자자 데이터", f"{result.investor_record_count:,}건")
    table.add_row("소요 시간", f"{elapsed_seconds:.2f}초")

    if not result.success:
        table.add_row("에러 메시지", result.error_message, style="red")

    if result.retry_count > 0:
        table.add_row("재시도 횟수", str(result.retry_count), style="yellow")

    return table


class SingleTickerProgressTracker:
    """단일 종목 수집 진행 상황 추적용 클래스"""

    def __init__(self, progress_task, progress_manager: Progress):
        self.collected = False
        self.result = None
        self.progress_task = progress_task
        self.progress_manager = progress_manager

    async def callback(self, ticker: str, result) -> None:
        """
        수집 진행 콜백 함수

        Args:
            ticker: 종목 코드
            result: 수집 결과 객체
        """
        self.progress_manager.update(self.progress_task, completed=50)
        self.collected = True
        self.result = result


async def collect_single_ticker(
    ticker: str,
    fromdate: date,
    todate: date,
    collect_investor: bool = True,
    force_full: bool = False,
    db_path: str = DEFAULT_DB_PATH
) -> Optional[object]:
    """
    단일 종목 데이터 수집

    Args:
        ticker: 종목 코드 (예: "005930", "025980")
        fromdate: 수집 시작일
        todate: 수집 종료일
        collect_investor: 투자자 데이터 수집 여부
        force_full: 전체 재수집 강제 (증분 수집 무시)
        db_path: 데이터베이스 파일 경로

    Returns:
        Optional[object]: 수집 결과 객체, 수집할 데이터가 없으면 None
    """
    start_time = datetime.now()

    console.print("\n" + "=" * SEPARATOR_WIDTH)
    console.print(f"[bold cyan]단일 종목 데이터 수집 시작[/bold cyan]")
    console.print("=" * SEPARATOR_WIDTH + "\n")

    # 1. DB 연결 및 테이블 생성
    console.print("[cyan]1. 데이터베이스 초기화...[/cyan]")
    db = get_db_connection(db_path)
    console.print(f"   [green]OK[/green] DB 연결 완료: {db_path}\n")

    # 2. 증분 수집 계획 수립
    console.print("[cyan]2. 수집 계획 수립...[/cyan]")
    incremental = IncrementalCollector(db)
    plans = incremental.get_collection_plan(
        tickers=[ticker],
        fromdate=fromdate,
        todate=todate,
        force_full=force_full
    )

    if not plans:
        console.print(f"   [yellow]WARNING[/yellow] 수집할 데이터가 없습니다 (이미 최신 상태)\n")
        return None

    plan = plans[0]
    console.print(f"   [green]OK[/green] 수집 계획:")
    console.print(f"     - 종목: {plan.ticker}")
    console.print(f"     - 기간: {plan.fromdate} ~ {plan.todate}")
    console.print(f"     - 전체 수집: {'예' if plan.is_full_collection else '아니오 (증분)'}")
    if plan.existing_latest_date:
        console.print(f"     - 기존 최신 날짜: {plan.existing_latest_date}")
    console.print()

    # 3. 비동기 수집 실행
    console.print("[cyan]3. 데이터 수집 중...[/cyan]")

    collector = AsyncUnifiedCollector(
        db_connection=db,
        delay=API_DELAY,
        concurrency=1,  # 단일 종목이므로 1
        max_retries=MAX_RETRIES
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task(
            f"   [{ticker}] 수집 중...",
            total=100
        )

        # ProgressTracker 초기화
        tracker = SingleTickerProgressTracker(task, progress)

        # 비동기 수집 실행
        results = await collector.collect_batch(
            tickers=[plan.ticker],
            fromdate=plan.fromdate,
            todate=plan.todate,
            collect_investor=collect_investor,
            progress_callback=tracker.callback
        )

        progress.update(task, completed=100)
        result = results[0] if results else None

    console.print()

    # 4. 결과 출력
    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()

    console.print("=" * SEPARATOR_WIDTH)
    console.print(f"[bold cyan]수집 완료[/bold cyan]")
    console.print("=" * SEPARATOR_WIDTH + "\n")

    if result:
        stats_table = create_stats_table(result, ticker, plan.fromdate, plan.todate, elapsed)
        console.print(stats_table)
        console.print()

        if result.success:
            console.print(Panel(
                f"[bold green]성공![/bold green]\n"
                f"주가 데이터: {result.price_record_count:,}건\n"
                f"투자자 데이터: {result.investor_record_count:,}건\n"
                f"소요 시간: {elapsed:.2f}초",
                title="수집 결과",
                border_style="green"
            ))
        else:
            console.print(Panel(
                f"[bold red]실패[/bold red]\n{result.error_message}",
                title="수집 결과",
                border_style="red"
            ))
    else:
        console.print("[red]수집 결과를 가져올 수 없습니다.[/red]")

    return result


def main() -> None:
    """CLI 진입점"""
    parser = argparse.ArgumentParser(
        description=f"단일 종목 데이터 수집 ({DEFAULT_FROM_DATE} ~ 현재)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 아난티(025980) 수집
  uv run python scripts/collect_single_ticker.py --ticker 025980

  # 삼성전자(005930) 수집 (투자자 데이터 제외)
  uv run python scripts/collect_single_ticker.py --ticker 005930 --no-investor

  # 전체 재수집 (증분 무시)
  uv run python scripts/collect_single_ticker.py --ticker 025980 --force-full
        """
    )

    parser.add_argument(
        "--ticker",
        type=str,
        required=True,
        help="종목 코드 (예: 005930, 025980)"
    )

    parser.add_argument(
        "--from-date",
        type=str,
        default=DEFAULT_FROM_DATE,
        help=f"시작 날짜 (YYYY-MM-DD, 기본값: {DEFAULT_FROM_DATE})"
    )

    parser.add_argument(
        "--to-date",
        type=str,
        default=None,
        help="종료 날짜 (YYYY-MM-DD, 기본값: 오늘)"
    )

    parser.add_argument(
        "--no-investor",
        action="store_true",
        help="투자자 데이터 수집 제외 (주가 데이터만 수집)"
    )

    parser.add_argument(
        "--force-full",
        action="store_true",
        help="전체 재수집 강제 (증분 수집 무시)"
    )

    parser.add_argument(
        "--db",
        type=str,
        default=DEFAULT_DB_PATH,
        help=f"데이터베이스 파일 경로 (기본값: {DEFAULT_DB_PATH})"
    )

    args = parser.parse_args()

    # 날짜 파싱
    try:
        fromdate = datetime.strptime(args.from_date, "%Y-%m-%d").date()
    except ValueError:
        console.print(f"[red]에러:[/red] 잘못된 시작 날짜 형식: {args.from_date}")
        sys.exit(1)

    if args.to_date:
        try:
            todate = datetime.strptime(args.to_date, "%Y-%m-%d").date()
        except ValueError:
            console.print(f"[red]에러:[/red] 잘못된 종료 날짜 형식: {args.to_date}")
            sys.exit(1)
    else:
        todate = date.today()

    # 비동기 수집 실행
    try:
        asyncio.run(collect_single_ticker(
            ticker=args.ticker,
            fromdate=fromdate,
            todate=todate,
            collect_investor=not args.no_investor,
            force_full=args.force_full,
            db_path=args.db
        ))
    except KeyboardInterrupt:
        console.print("\n[yellow]사용자에 의해 중단되었습니다.[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]에러 발생:[/red] {e}")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
