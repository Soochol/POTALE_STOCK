"""
YAML 기반 동적 블록 패턴 탐지 스크립트

YAML 설정 파일로부터 블록 정의를 읽어 주가 데이터에서 블록 패턴을 탐지합니다.

Features:
- YAML 기반 다이나믹 블록 탐지
- 무제한 블록 타입 지원 (Block1~Block99+)
- ExpressionEngine으로 조건 평가
- dynamic_block_detection 테이블에 저장
- Rich 라이브러리로 결과 시각화

Usage:
    # 기본: extended_pattern_example.yaml로 탐지
    python scripts/rule_based_detection/detect_patterns.py \\
        --ticker 025980 \\
        --config presets/examples/extended_pattern_example.yaml

    # 다중 종목
    python scripts/rule_based_detection/detect_patterns.py \\
        --ticker 025980,005930,035720 \\
        --config presets/examples/extended_pattern_example.yaml

    # 기간 지정
    python scripts/rule_based_detection/detect_patterns.py \\
        --ticker 025980 \\
        --config presets/examples/extended_pattern_example.yaml \\
        --from-date 2020-01-01

    # 상세 출력
    python scripts/rule_based_detection/detect_patterns.py \\
        --ticker 025980 \\
        --config presets/examples/extended_pattern_example.yaml \\
        --verbose

    # 미리보기만 (저장 안 함)
    python scripts/rule_based_detection/detect_patterns.py \\
        --ticker 025980 \\
        --config presets/examples/simple_pattern_example.yaml \\
        --dry-run
"""
import argparse
import os
import sys
from datetime import date, datetime
from pathlib import Path
from typing import List

from loguru import logger
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Constants
DEFAULT_DB_PATH = 'data/database/stock_data.db'
DEFAULT_FROM_DATE = date(2015, 1, 1)
SEPARATOR_WIDTH = 80

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

from src.application.services.block_graph_loader import BlockGraphLoader
from src.application.use_cases.dynamic_block_detector import DynamicBlockDetector
from src.application.services.indicators.block1_indicator_calculator import Block1IndicatorCalculator
from src.domain.entities.conditions import ExpressionEngine, function_registry
from src.domain.entities.detections import DynamicBlockDetection
from src.infrastructure.database.connection import get_db_connection
from src.infrastructure.repositories.dynamic_block_repository_impl import (
    DynamicBlockRepositoryImpl,
)
from src.infrastructure.repositories.stock.sqlite_stock_repository import (
    SqliteStockRepository,
)

# Loguru 설정
logger.remove()  # 기본 핸들러 제거
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO",
    colorize=True
)

console = Console()


def create_results_table(detections: List[DynamicBlockDetection], ticker: str) -> Table:
    """
    탐지 결과를 Rich Table로 생성

    Args:
        detections: 탐지된 블록 리스트
        ticker: 종목 코드

    Returns:
        Table: 탐지 결과 테이블
    """
    table = Table(
        title=f"Dynamic Block Detection Results - {ticker}",
        show_header=True,
        header_style="bold cyan",
        title_style="bold yellow",
        box=box.ROUNDED
    )

    table.add_column("Block Type", style="cyan", width=12, justify="center")
    table.add_column("Block ID", style="dim", width=15, justify="left")
    table.add_column("Started", style="green", width=12, justify="center")
    table.add_column("Ended", style="yellow", width=12, justify="center")
    table.add_column("Peak Price", style="magenta", width=12, justify="right")
    table.add_column("Peak Volume", style="blue", width=14, justify="right")
    table.add_column("Status", style="bold", width=10, justify="center")

    # 블록 타입별로 정렬
    sorted_detections = sorted(detections, key=lambda x: (x.block_type, x.started_at))

    for detection in sorted_detections:
        block_type_str = f"Block{detection.block_type}"
        ended_str = str(detection.ended_at) if detection.ended_at else "Active"
        peak_price_str = f"{detection.peak_price:,.0f}원" if detection.peak_price else "-"
        peak_volume_str = f"{detection.peak_volume:,}" if detection.peak_volume else "-"

        status_style = "green" if detection.status.value == "completed" else "yellow"
        status_str = f"[{status_style}]{detection.status.value.upper()}[/{status_style}]"

        table.add_row(
            block_type_str,
            detection.block_id,
            str(detection.started_at) if detection.started_at else "-",
            ended_str,
            peak_price_str,
            peak_volume_str,
            status_str
        )

    return table


def create_summary_panel(
    ticker: str,
    config_path: str,
    from_date: date,
    to_date: date,
    total_blocks: int,
    by_type: dict,
    elapsed_seconds: float
) -> Panel:
    """
    요약 패널 생성

    Args:
        ticker: 종목 코드
        config_path: YAML 설정 파일 경로
        from_date: 시작 날짜
        to_date: 종료 날짜
        total_blocks: 총 탐지된 블록 수
        by_type: 블록 타입별 개수 딕셔너리
        elapsed_seconds: 소요 시간(초)

    Returns:
        Panel: 요약 패널
    """
    by_type_str = ", ".join([f"Block{k}: {v}" for k, v in sorted(by_type.items())])

    content = (
        f"[bold cyan]Ticker:[/bold cyan] {ticker}\n"
        f"[bold cyan]Config:[/bold cyan] {config_path}\n"
        f"[bold cyan]Period:[/bold cyan] {from_date} ~ {to_date}\n\n"
        f"[bold green]Total Blocks Detected:[/bold green] {total_blocks}\n"
        f"[bold yellow]By Type:[/bold yellow] {by_type_str}\n\n"
        f"[bold magenta]Elapsed Time:[/bold magenta] {elapsed_seconds:.2f}s"
    )

    return Panel(
        content,
        title="[bold yellow]Detection Summary[/bold yellow]",
        border_style="yellow",
        box=box.DOUBLE
    )


def detect_patterns_for_ticker(
    ticker: str,
    config_path: str,
    from_date: date,
    to_date: date,
    db_path: str,
    verbose: bool = False,
    dry_run: bool = False
) -> List[DynamicBlockDetection]:
    """
    단일 종목에 대한 블록 패턴 탐지

    Args:
        ticker: 종목 코드
        config_path: YAML 설정 파일 경로
        from_date: 시작 날짜
        to_date: 종료 날짜
        db_path: 데이터베이스 파일 경로
        verbose: 상세 출력 여부
        dry_run: 저장하지 않고 미리보기만

    Returns:
        List[DynamicBlockDetection]: 탐지된 블록 리스트
    """
    start_time = datetime.now()

    console.print(f"\n[bold cyan]{'='*SEPARATOR_WIDTH}[/bold cyan]")
    console.print(f"[bold cyan]Dynamic Block Detection - {ticker}[/bold cyan]")
    console.print(f"[bold cyan]{'='*SEPARATOR_WIDTH}[/bold cyan]\n")

    # 1. YAML 로드
    console.print("[cyan]1. Loading BlockGraph from YAML...[/cyan]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"   Loading {config_path}...", total=None)

        try:
            loader = BlockGraphLoader()
            block_graph = loader.load_from_file(config_path)
            progress.update(task, completed=True)

            if verbose:
                console.print(f"   [green]OK[/green] Loaded {len(block_graph.nodes)} nodes, {len(block_graph.edges)} edges\n")
            else:
                console.print(f"   [green]OK[/green] BlockGraph loaded\n")
        except Exception as e:
            console.print(f"   [red]ERROR[/red] Failed to load YAML: {e}\n")
            raise

    # 2. 데이터베이스 연결
    console.print("[cyan]2. Connecting to database...[/cyan]")
    db = get_db_connection(db_path)
    session = db.get_session()
    console.print(f"   [green]OK[/green] Connected to {db_path}\n")

    # 3. 주가 데이터 로드
    console.print("[cyan]3. Loading stock data...[/cyan]")
    stock_repo = SqliteStockRepository()
    stocks = stock_repo.get_stock_data(
        ticker=ticker,
        start_date=from_date,
        end_date=to_date
    )

    if not stocks:
        console.print(f"   [red]ERROR[/red] No stock data found for {ticker}\n")
        return []

    if verbose:
        console.print(f"   [green]OK[/green] Loaded {len(stocks)} price records ({stocks[0].date} ~ {stocks[-1].date})\n")
    else:
        console.print(f"   [green]OK[/green] Loaded {len(stocks)} records\n")

    # 3.5. 지표 계산 (365일 신고가 등)
    console.print("[cyan]3.5. Calculating indicators...[/cyan]")
    indicator_calculator = Block1IndicatorCalculator()
    stocks = indicator_calculator.calculate(
        stocks=stocks,
        new_high_days=365  # 365일 신고가 계산
    )
    console.print(f"   [green]OK[/green] Indicators calculated\n")

    # 4. 블록 탐지
    console.print("[cyan]4. Detecting blocks...[/cyan]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("   Running detection...", total=None)

        try:
            expression_engine = ExpressionEngine(function_registry)
            detector = DynamicBlockDetector(block_graph, expression_engine)

            detections = detector.detect_blocks(
                ticker=ticker,
                stocks=stocks,
                condition_name="seed"
            )

            progress.update(task, completed=True)
            console.print(f"   [green]OK[/green] Detected {len(detections)} blocks\n")
        except Exception as e:
            console.print(f"   [red]ERROR[/red] Detection failed: {e}\n")
            raise

    # 5. 데이터베이스 저장 (dry-run이 아닌 경우)
    if not dry_run and detections:
        console.print("[cyan]5. Saving to database...[/cyan]")
        try:
            repo = DynamicBlockRepositoryImpl(session)
            saved_detections = repo.save_all(detections)
            console.print(f"   [green]OK[/green] Saved {len(saved_detections)} blocks to dynamic_block_detection\n")
        except Exception as e:
            console.print(f"   [red]ERROR[/red] Save failed: {e}\n")
            raise
    elif dry_run:
        console.print("[yellow]5. Skipping save (dry-run mode)[/yellow]\n")

    # 6. 결과 출력
    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()

    if detections:
        # 타입별 집계
        by_type = {}
        for detection in detections:
            by_type[detection.block_type] = by_type.get(detection.block_type, 0) + 1

        # 요약 패널
        summary_panel = create_summary_panel(
            ticker=ticker,
            config_path=config_path,
            from_date=from_date,
            to_date=to_date,
            total_blocks=len(detections),
            by_type=by_type,
            elapsed_seconds=elapsed
        )
        console.print(summary_panel)
        console.print()

        # 상세 테이블
        results_table = create_results_table(detections, ticker)
        console.print(results_table)
        console.print()
    else:
        console.print("[yellow]No blocks detected.[/yellow]\n")

    session.close()
    return detections


def main() -> None:
    """CLI 진입점"""
    parser = argparse.ArgumentParser(
        description="YAML 기반 동적 블록 패턴 탐지",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 기본 사용법
  python detect_patterns.py --ticker 025980 --config presets/examples/extended_pattern_example.yaml

  # 다중 종목
  python detect_patterns.py --ticker 025980,005930 --config presets/examples/extended_pattern_example.yaml

  # 기간 지정
  python detect_patterns.py --ticker 025980 --config presets/examples/extended_pattern_example.yaml --from-date 2020-01-01

  # 상세 출력
  python detect_patterns.py --ticker 025980 --config presets/examples/extended_pattern_example.yaml --verbose

  # 미리보기 (저장 안 함)
  python detect_patterns.py --ticker 025980 --config presets/examples/simple_pattern_example.yaml --dry-run
        """
    )

    parser.add_argument(
        "--ticker",
        type=str,
        required=True,
        help="종목 코드 (쉼표로 구분, 예: 025980,005930)"
    )

    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="YAML 설정 파일 경로 (예: presets/examples/extended_pattern_example.yaml)"
    )

    parser.add_argument(
        "--from-date",
        type=str,
        default=None,
        help=f"시작 날짜 (YYYY-MM-DD, 기본값: {DEFAULT_FROM_DATE})"
    )

    parser.add_argument(
        "--to-date",
        type=str,
        default=None,
        help="종료 날짜 (YYYY-MM-DD, 기본값: 오늘)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="상세 출력"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="미리보기만 (저장 안 함)"
    )

    parser.add_argument(
        "--db",
        type=str,
        default=DEFAULT_DB_PATH,
        help=f"데이터베이스 파일 경로 (기본값: {DEFAULT_DB_PATH})"
    )

    args = parser.parse_args()

    # 날짜 파싱
    if args.from_date:
        try:
            from_date = datetime.strptime(args.from_date, "%Y-%m-%d").date()
        except ValueError:
            console.print(f"[red]에러:[/red] 잘못된 시작 날짜 형식: {args.from_date}")
            sys.exit(1)
    else:
        from_date = DEFAULT_FROM_DATE

    if args.to_date:
        try:
            to_date = datetime.strptime(args.to_date, "%Y-%m-%d").date()
        except ValueError:
            console.print(f"[red]에러:[/red] 잘못된 종료 날짜 형식: {args.to_date}")
            sys.exit(1)
    else:
        to_date = date.today()

    # YAML 파일 존재 확인
    config_path = Path(args.config)
    if not config_path.exists():
        console.print(f"[red]에러:[/red] YAML 파일을 찾을 수 없습니다: {args.config}")
        sys.exit(1)

    # 종목 코드 파싱
    tickers = [t.strip() for t in args.ticker.split(',')]

    # 각 종목별 탐지 실행
    try:
        for ticker in tickers:
            detect_patterns_for_ticker(
                ticker=ticker,
                config_path=str(config_path),
                from_date=from_date,
                to_date=to_date,
                db_path=args.db,
                verbose=args.verbose,
                dry_run=args.dry_run
            )

            # 다음 종목 전에 구분선
            if len(tickers) > 1:
                console.print("\n" + "="*SEPARATOR_WIDTH + "\n")

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
