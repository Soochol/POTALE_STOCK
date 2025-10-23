"""
전체 종목 데이터 수집 스크립트

KOSPI + KOSDAQ 전체 종목 또는 지정된 종목의 주가 및 투자자 데이터를 수집합니다.

Features:
- 전체 종목 자동 수집 (네이버 금융 API)
- 특정 종목 선택 가능 (쉼표로 구분)
- 증분 수집 지원 (이미 수집된 데이터는 건너뛰기)
- 병렬 수집 (동시 처리 종목 수 설정 가능)
- 주가 데이터 + 투자자 데이터 동시 수집
- Rich 라이브러리로 진행 상황 시각화
- 데이터베이스 자동 초기화

Usage:
    # 전체 종목 수집 (KOSPI + KOSDAQ)
    uv run python scripts/collect_all_tickers.py

    # 특정 종목만 수집
    uv run python scripts/collect_all_tickers.py --ticker 025980,005930,035720

    # 기간 지정
    uv run python scripts/collect_all_tickers.py --from-date 2020-01-01

    # 동시 처리 종목 수 증가 (성능 향상)
    uv run python scripts/collect_all_tickers.py --concurrency 20

    # 투자자 데이터 제외 (주가만)
    uv run python scripts/collect_all_tickers.py --no-investor

    # 전체 재수집 (증분 무시)
    uv run python scripts/collect_all_tickers.py --force-full
"""
import argparse
import asyncio
import os
import sys
import traceback
from datetime import date, datetime
from pathlib import Path
from typing import Any, List, Optional, Tuple

from loguru import logger
from rich import box
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
DEFAULT_CONCURRENCY = 10
DEFAULT_DB_PATH = "data/database/stock_data.db"
API_DELAY = 0.1
MAX_RETRIES = 3
MAX_BATCH_SIZE = 100
SEPARATOR_WIDTH = 80
MAX_SAMPLE_TICKERS = 10
MAX_FAILED_DISPLAY = 15
MAX_ERROR_MSG_LENGTH = 58
MIN_SAMPLE_COUNT = 5
MAX_SAMPLE_DISPLAY = 10
MAX_TICKER_DISPLAY = 10
EXIT_ERROR = 1
EXIT_KEYBOARD_INTERRUPT = 130

# Error messages
ERROR_MSG_INVALID_DATE = "[red]에러:[/red] 잘못된 {field} 형식: {value}"
ERROR_MSG_NO_TICKERS = "[red]에러:[/red] 종목이 없습니다."
ERROR_MSG_INTERRUPTED = "\n[yellow]사용자에 의해 중단되었습니다.[/yellow]"
ERROR_MSG_EXCEPTION = "\n[red]에러 발생:[/red] {error}"

# Windows 콘솔 UTF-8 설정
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.collectors.incremental_collector import IncrementalCollector
from src.infrastructure.collectors.naver.async_unified_collector import (
    AsyncUnifiedCollector,
)
from src.infrastructure.database.connection import get_db_connection
from src.infrastructure.utils.naver_ticker_list import get_all_tickers

# Loguru 설정
logger.remove()  # 기본 핸들러 제거
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO",
    colorize=True
)

console = Console()


def create_collection_plan_panel(
    total_tickers: int,
    plans_count: int,
    full_count: int,
    incremental_count: int,
    skipped_count: int,
    fromdate: date,
    todate: date,
    concurrency: int
) -> Panel:
    """
    수집 계획을 시각화한 Rich Panel 생성

    Args:
        total_tickers: 전체 종목 수
        plans_count: 수집 계획된 종목 수
        full_count: 전체 수집 대상 종목 수
        incremental_count: 증분 수집 대상 종목 수
        skipped_count: 건너뛸 종목 수
        fromdate: 수집 시작 날짜
        todate: 수집 종료 날짜
        concurrency: 동시 처리 종목 수

    Returns:
        Panel: 수집 계획 정보가 담긴 Rich Panel 객체
    """
    content = (
        f"[bold cyan]📊 수집 대상[/bold cyan]\n"
        f"  총 종목:     [bold]{total_tickers:>6,}[/bold]개\n"
        f"  수집 필요:   [green]{plans_count:>6,}[/green]개\n"
        f"    ├─ 전체 수집: [yellow]{full_count:>6,}[/yellow]개 (신규)\n"
        f"    └─ 증분 수집: [cyan]{incremental_count:>6,}[/cyan]개 (업데이트)\n"
        f"  건너뛰기:    [dim]{skipped_count:>6,}[/dim]개 (이미 최신)\n\n"
        f"[bold cyan]📅 수집 기간[/bold cyan]\n"
        f"  {fromdate} ~ {todate}\n\n"
        f"[bold cyan]⚡ 성능 설정[/bold cyan]\n"
        f"  동시 처리:   [bold]{concurrency}[/bold]개 종목"
    )
    return Panel(
        content,
        title="[bold yellow]수집 계획[/bold yellow]",
        border_style="yellow",
        box=box.DOUBLE
    )


def create_stats_table(
    total_tickers: int,
    successful: int,
    failed: int,
    total_price_records: int,
    total_investor_records: int,
    elapsed_seconds: float
) -> Table:
    """
    수집 결과 통계를 요약한 Rich Table 생성

    Args:
        total_tickers: 전체 처리 종목 수
        successful: 성공한 종목 수
        failed: 실패한 종목 수
        total_price_records: 수집된 주가 데이터 건수
        total_investor_records: 수집된 투자자 데이터 건수
        elapsed_seconds: 소요 시간(초)

    Returns:
        Table: 수집 통계 정보가 담긴 Rich Table 객체
    """
    table = Table(
        title="📈 수집 결과 요약",
        show_header=True,
        header_style="bold magenta",
        title_style="bold cyan",
        box=box.DOUBLE_EDGE
    )
    table.add_column("항목", style="bold cyan", width=25, justify="left")
    table.add_column("값", style="bold", width=30, justify="right")

    # 성공률 계산
    success_rate = (successful / total_tickers * 100) if total_tickers > 0 else 0

    table.add_row("총 종목 수", f"{total_tickers:,}개")
    table.add_row("성공", f"[green]{successful:,}개[/green]")
    table.add_row("성공률", f"[green]{success_rate:.1f}%[/green]")

    if failed > 0:
        table.add_row("실패", f"[red]{failed:,}개[/red]")

    table.add_row("", "")  # 구분선
    table.add_row("주가 데이터", f"[cyan]{total_price_records:,}[/cyan]건")
    table.add_row("투자자 데이터", f"[cyan]{total_investor_records:,}[/cyan]건")
    table.add_row("총 데이터", f"[bold green]{total_price_records + total_investor_records:,}[/bold green]건")

    table.add_row("", "")  # 구분선
    table.add_row("소요 시간", f"[yellow]{elapsed_seconds:.2f}[/yellow]초")

    if successful > 0:
        avg_time = elapsed_seconds / successful
        throughput = successful / elapsed_seconds * 60 if elapsed_seconds > 0 else 0
        table.add_row("평균 처리 시간", f"[yellow]{avg_time:.2f}[/yellow]초/종목")
        table.add_row("처리량", f"[yellow]{throughput:.1f}[/yellow]개/분")

    return table


def create_successful_tickers_table(successful_results: List, max_display: int = MAX_SAMPLE_TICKERS) -> Table:
    """
    성공한 종목 샘플 테이블 생성

    Args:
        successful_results: 성공한 수집 결과 리스트
        max_display: 최대 표시 건수

    Returns:
        Table: 성공한 종목 샘플 정보가 담긴 Rich Table 객체
    """
    table = Table(
        title=f"✅ 성공한 종목 (샘플 {min(max_display, len(successful_results))}개)",
        show_header=True,
        header_style="bold green",
        title_style="bold green",
        box=box.ROUNDED
    )
    table.add_column("종목 코드", style="cyan", width=12, justify="center")
    table.add_column("주가 데이터", style="green", width=15, justify="right")
    table.add_column("투자자 데이터", style="blue", width=15, justify="right")
    table.add_column("재시도", style="yellow", width=10, justify="center")

    for result in successful_results[:max_display]:
        retry_display = f"{result.retry_count}회" if result.retry_count > 0 else "-"
        table.add_row(
            result.ticker,
            f"{result.price_record_count:,}건",
            f"{result.investor_record_count:,}건",
            retry_display
        )

    if len(successful_results) > max_display:
        table.add_row("...", f"외 {len(successful_results) - max_display}개", "", "")

    return table


def create_failed_tickers_table(failed_results: List, max_display: int = MAX_FAILED_DISPLAY) -> Table:
    """
    실패한 종목 테이블 생성

    Args:
        failed_results: 실패한 수집 결과 리스트
        max_display: 최대 표시 건수

    Returns:
        Table: 실패한 종목 정보가 담긴 Rich Table 객체
    """
    table = Table(
        title=f"❌ 실패한 종목 ({len(failed_results)}개)",
        show_header=True,
        header_style="bold red",
        title_style="bold red",
        box=box.HEAVY_EDGE
    )
    table.add_column("No.", style="dim", width=5, justify="right")
    table.add_column("종목 코드", style="cyan", width=12, justify="center")
    table.add_column("에러 메시지", style="yellow", width=58, justify="left")

    for idx, result in enumerate(failed_results[:max_display], 1):
        error_msg = result.error_message or "알 수 없는 에러"
        # 에러 메시지가 너무 길면 잘라내기
        if len(error_msg) > MAX_ERROR_MSG_LENGTH:
            error_msg = error_msg[:MAX_ERROR_MSG_LENGTH - 3] + "..."
        table.add_row(str(idx), result.ticker, error_msg)

    if len(failed_results) > max_display:
        table.add_row("...", "...", f"외 {len(failed_results) - max_display}개 더 있음")

    return table


def parse_date_argument(date_str: Optional[str], field_name: str, default: Optional[date] = None) -> date:
    """
    날짜 인자를 파싱

    Args:
        date_str: 날짜 문자열 (YYYY-MM-DD 형식)
        field_name: 필드 이름 (에러 메시지용)
        default: 기본값 (None이면 오늘 날짜)

    Returns:
        date: 파싱된 날짜 객체

    Raises:
        SystemExit: 날짜 형식이 잘못된 경우
    """
    if date_str is None:
        return default if default is not None else date.today()

    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        console.print(ERROR_MSG_INVALID_DATE.format(field=field_name, value=date_str))
        sys.exit(EXIT_ERROR)


def get_ticker_list(ticker_arg: Optional[str]) -> List[str]:
    """
    종목 리스트 로드

    Args:
        ticker_arg: 종목 코드 인자 (쉼표로 구분된 문자열)

    Returns:
        List[str]: 종목 코드 리스트

    Raises:
        SystemExit: 종목이 없는 경우
    """
    if ticker_arg:
        # 특정 종목만 수집
        tickers = [t.strip() for t in ticker_arg.split(',')]
        logger.info(f"특정 종목 수집 모드: {len(tickers)}개")
        console.print(f"\n[bold cyan]📌 특정 종목 수집 모드[/bold cyan]")
        console.print(f"   종목 수: [bold]{len(tickers)}[/bold]개")
        if len(tickers) <= MAX_TICKER_DISPLAY:
            console.print(f"   종목: [cyan]{', '.join(tickers)}[/cyan]\n")
        else:
            console.print(f"   종목: [cyan]{', '.join(tickers[:MAX_TICKER_DISPLAY])}[/cyan] 외 {len(tickers)-MAX_TICKER_DISPLAY}개\n")
    else:
        # 전체 종목 수집
        logger.info("전체 종목 리스트 로딩 중...")
        console.print(f"\n[bold cyan]🌐 전체 종목 수집 모드[/bold cyan]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("   네이버 금융에서 종목 리스트 로딩 중...", total=None)
            tickers = get_all_tickers()

        logger.success(f"종목 리스트 로딩 완료: {len(tickers)}개")
        console.print(f"   [green]✓[/green] 총 [bold cyan]{len(tickers):,}[/bold cyan]개 종목 발견\n")

    if not tickers:
        console.print(ERROR_MSG_NO_TICKERS)
        sys.exit(EXIT_ERROR)

    return tickers


class ProgressTracker:
    """수집 진행 상황 추적용 헬퍼 클래스"""

    def __init__(self, progress_task: Any, progress_manager: Progress) -> None:
        """
        ProgressTracker 초기화

        Args:
            progress_task: Progress task 객체
            progress_manager: Progress manager 객체
        """
        self.completed_count = 0
        self.success_count = 0
        self.fail_count = 0
        self.progress_task = progress_task
        self.progress_manager = progress_manager

    async def callback(self, ticker: str, result: Any) -> None:
        """
        수집 진행 콜백 함수

        Args:
            ticker: 종목 코드
            result: 수집 결과 객체
        """
        self.completed_count += 1
        if result.success:
            self.success_count += 1
        else:
            self.fail_count += 1
        self.progress_manager.update(
            self.progress_task,
            completed=self.completed_count,
            success=self.success_count,
            fail=self.fail_count
        )


async def collect_all_tickers_main(
    tickers: List[str],
    fromdate: date,
    todate: date,
    collect_investor: bool = True,
    force_full: bool = False,
    concurrency: int = DEFAULT_CONCURRENCY,
    db_path: str = DEFAULT_DB_PATH
) -> None:
    """
    전체 종목 데이터 수집

    Args:
        tickers: 종목 코드 리스트
        fromdate: 수집 시작일
        todate: 수집 종료일
        collect_investor: 투자자 데이터 수집 여부
        force_full: 전체 재수집 강제 (증분 수집 무시)
        concurrency: 동시 처리 종목 수
        db_path: 데이터베이스 파일 경로
    """
    start_time = datetime.now()

    console.print("\n" + "=" * SEPARATOR_WIDTH)
    console.print(f"[bold cyan]📦 전체 종목 데이터 수집 시작[/bold cyan]")
    console.print("=" * SEPARATOR_WIDTH + "\n")

    # 1. DB 연결 및 테이블 생성
    logger.info("데이터베이스 초기화 중...")
    console.print("[bold cyan]1. 데이터베이스 초기화...[/bold cyan]")
    db = get_db_connection(db_path)
    logger.success(f"DB 연결 완료: {db_path}")
    console.print(f"   [green]✓[/green] DB 연결 완료: [dim]{db_path}[/dim]\n")

    # 2. 증분 수집 계획 수립
    logger.info("수집 계획 수립 중...")
    console.print("[bold cyan]2. 수집 계획 수립...[/bold cyan]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("   종목 분석 중...", total=None)
        incremental = IncrementalCollector(db)
        plans = incremental.get_collection_plan(
            tickers=tickers,
            fromdate=fromdate,
            todate=todate,
            force_full=force_full
        )

    if not plans:
        logger.warning("수집할 데이터 없음 (모든 종목이 최신 상태)")
        console.print(f"   [yellow]⚠[/yellow] 수집할 데이터가 없습니다\n")
        console.print(Panel(
            f"[bold green]✅ 완료![/bold green]\n\n"
            f"모든 종목이 [cyan]{todate}[/cyan]까지 최신 상태입니다.",
            title="[bold green]수집 완료[/bold green]",
            border_style="green",
            box=box.DOUBLE
        ))
        return

    # 수집 계획 요약
    full_count = sum(1 for p in plans if p.is_full_collection)
    incremental_count = len(plans) - full_count
    skipped_count = len(tickers) - len(plans)

    logger.success(f"수집 계획 수립 완료: {len(plans)}개 종목")
    console.print(f"   [green]✓[/green] 계획 수립 완료\n")

    # 수집 계획 패널 표시
    plan_panel = create_collection_plan_panel(
        total_tickers=len(tickers),
        plans_count=len(plans),
        full_count=full_count,
        incremental_count=incremental_count,
        skipped_count=skipped_count,
        fromdate=fromdate,
        todate=todate,
        concurrency=concurrency
    )
    console.print(plan_panel)
    console.print()

    # 3. 비동기 배치 수집 실행
    logger.info(f"데이터 수집 시작: {len(plans)}개 종목")
    console.print("[bold cyan]3. 데이터 수집 실행...[/bold cyan]\n")

    collector = AsyncUnifiedCollector(
        db_connection=db,
        delay=API_DELAY,
        concurrency=concurrency,
        max_retries=MAX_RETRIES
    )

    # 진행 상황 추적
    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("•"),
        TextColumn("[cyan]{task.completed}[/cyan]/[blue]{task.total}[/blue]"),
        TextColumn("•"),
        TextColumn("[green]✓{task.fields[success]}[/green]"),
        TextColumn("[red]✗{task.fields[fail]}[/red]"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        # 전체 진행 상황 표시
        main_task = progress.add_task(
            "   [bold]수집 진행[/bold]",
            total=len(plans),
            success=0,
            fail=0
        )

        # ProgressTracker 초기화
        tracker = ProgressTracker(main_task, progress)

        # 배치로 나눠서 수집 (메모리 관리)
        batch_size = min(MAX_BATCH_SIZE, len(plans))

        for i in range(0, len(plans), batch_size):
            batch_plans = plans[i:i + batch_size]
            batch_tickers = [p.ticker for p in batch_plans]

            # 배치 수집 실행
            batch_results = await collector.collect_batch(
                tickers=batch_tickers,
                fromdate=fromdate,
                todate=todate,
                collect_investor=collect_investor,
                progress_callback=tracker.callback
            )

            results.extend(batch_results)

        progress.update(main_task, completed=len(plans))

    logger.success(f"수집 완료: 성공 {tracker.success_count}개, 실패 {tracker.fail_count}개")
    console.print()

    # 4. 결과 집계
    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()

    successful_results = [r for r in results if r.success]
    failed_results = [r for r in results if not r.success]

    total_price_records = sum(r.price_record_count for r in results)
    total_investor_records = sum(r.investor_record_count for r in results)

    logger.info(f"결과 집계: 총 {len(results)}개 처리")

    # 5. 결과 출력
    console.print("\n" + "=" * SEPARATOR_WIDTH)
    console.print(f"[bold cyan]📊 수집 완료[/bold cyan]")
    console.print("=" * SEPARATOR_WIDTH + "\n")

    # 요약 테이블
    stats_table = create_stats_table(
        total_tickers=len(plans),
        successful=len(successful_results),
        failed=len(failed_results),
        total_price_records=total_price_records,
        total_investor_records=total_investor_records,
        elapsed_seconds=elapsed
    )
    console.print(stats_table)
    console.print()

    # 성공한 종목 샘플 표시 (MIN_SAMPLE_COUNT개 이상일 때만)
    if len(successful_results) >= MIN_SAMPLE_COUNT:
        success_table = create_successful_tickers_table(successful_results, max_display=MAX_SAMPLE_DISPLAY)
        console.print(success_table)
        console.print()

    # 실패한 종목이 있으면 표시
    if failed_results:
        failed_table = create_failed_tickers_table(failed_results)
        console.print(failed_table)
        console.print()

    # 최종 요약 패널
    if len(failed_results) == 0:
        logger.success("모든 종목 수집 완료!")
        console.print(Panel(
            f"[bold green]✅ 완료![/bold green]\n\n"
            f"총 [bold cyan]{len(successful_results):,}[/bold cyan]개 종목 수집 완료\n\n"
            f"[cyan]📈 수집 데이터[/cyan]\n"
            f"  • 주가 데이터:     [bold]{total_price_records:>10,}[/bold]건\n"
            f"  • 투자자 데이터:   [bold]{total_investor_records:>10,}[/bold]건\n"
            f"  • 총 데이터:       [bold green]{total_price_records + total_investor_records:>10,}[/bold green]건\n\n"
            f"[yellow]⏱ 소요 시간:[/yellow] {elapsed:.2f}초 "
            f"([dim]{elapsed/60:.1f}분[/dim])",
            title="[bold green]🎉 수집 성공[/bold green]",
            border_style="green",
            box=box.DOUBLE
        ))
    else:
        logger.warning(f"부분 성공: 성공 {len(successful_results)}개, 실패 {len(failed_results)}개")
        console.print(Panel(
            f"[bold yellow]⚠ 부분 성공[/bold yellow]\n\n"
            f"[green]성공:[/green] [bold]{len(successful_results):,}[/bold]개  "
            f"[red]실패:[/red] [bold]{len(failed_results):,}[/bold]개\n\n"
            f"[cyan]📈 수집 데이터[/cyan]\n"
            f"  • 주가 데이터:     [bold]{total_price_records:>10,}[/bold]건\n"
            f"  • 투자자 데이터:   [bold]{total_investor_records:>10,}[/bold]건\n"
            f"  • 총 데이터:       [bold green]{total_price_records + total_investor_records:>10,}[/bold green]건\n\n"
            f"[yellow]⏱ 소요 시간:[/yellow] {elapsed:.2f}초 "
            f"([dim]{elapsed/60:.1f}분[/dim])",
            title="[bold yellow]📦 수집 결과[/bold yellow]",
            border_style="yellow",
            box=box.DOUBLE
        ))


def main() -> None:
    """CLI 진입점"""
    parser = argparse.ArgumentParser(
        description="전체 종목 데이터 수집 (KOSPI + KOSDAQ)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 전체 종목 수집 (KOSPI + KOSDAQ)
  uv run python scripts/collect_all_tickers.py

  # 특정 종목만 수집
  uv run python scripts/collect_all_tickers.py --ticker 025980,005930,035720

  # 기간 지정
  uv run python scripts/collect_all_tickers.py --from-date 2020-01-01 --to-date 2024-12-31

  # 동시 처리 종목 수 증가 (성능 향상)
  uv run python scripts/collect_all_tickers.py --concurrency 20

  # 투자자 데이터 제외 (주가만)
  uv run python scripts/collect_all_tickers.py --no-investor

  # 전체 재수집 (증분 무시)
  uv run python scripts/collect_all_tickers.py --ticker 025980 --force-full
        """
    )

    parser.add_argument(
        "--ticker",
        type=str,
        default=None,
        help="종목 코드 (쉼표로 구분, 예: 025980,005930). 생략시 전체 종목"
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
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help=f"동시 처리 종목 수 (기본값: {DEFAULT_CONCURRENCY}, 권장: 10-20)"
    )

    parser.add_argument(
        "--db",
        type=str,
        default=DEFAULT_DB_PATH,
        help=f"데이터베이스 파일 경로 (기본값: {DEFAULT_DB_PATH})"
    )

    args = parser.parse_args()

    # 날짜 파싱
    fromdate = parse_date_argument(args.from_date, "시작 날짜")
    todate = parse_date_argument(args.to_date, "종료 날짜")

    # 종목 코드 리스트 로드
    tickers = get_ticker_list(args.ticker)

    # 비동기 수집 실행
    try:
        asyncio.run(collect_all_tickers_main(
            tickers=tickers,
            fromdate=fromdate,
            todate=todate,
            collect_investor=not args.no_investor,
            force_full=args.force_full,
            concurrency=args.concurrency,
            db_path=args.db
        ))
    except KeyboardInterrupt:
        console.print(ERROR_MSG_INTERRUPTED)
        sys.exit(EXIT_KEYBOARD_INTERRUPT)
    except Exception as e:
        console.print(ERROR_MSG_EXCEPTION.format(error=e))
        console.print(traceback.format_exc())
        sys.exit(EXIT_ERROR)


if __name__ == "__main__":
    main()
