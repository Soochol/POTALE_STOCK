"""
블록 패턴 탐지 스크립트

데이터베이스에 저장된 주가 데이터로부터 Block1/2/3/4 패턴을 탐지합니다.

Features:
- Seed 탐지 + 5년 재탐지 통합 실행
- 단일/다중 종목 지원
- 프리셋 선택 가능
- Rich 라이브러리로 결과 시각화
- 데이터베이스에 자동 저장

Usage:
    # 기본: 아난티(025980) 전체 기간 탐지
    uv run python scripts/detect_patterns.py --ticker 025980

    # 다중 종목
    uv run python scripts/detect_patterns.py --ticker 025980,005930,035720

    # 기간 지정
    uv run python scripts/detect_patterns.py --ticker 025980 --from-date 2020-01-01

    # 다른 프리셋 사용
    uv run python scripts/detect_patterns.py --ticker 025980 --seed-preset strict_seed

    # 상세 출력
    uv run python scripts/detect_patterns.py --ticker 025980 --verbose

    # 미리보기만 (저장 안 함)
    uv run python scripts/detect_patterns.py --ticker 025980 --dry-run
"""
import sys
import os
import argparse
from pathlib import Path
from datetime import date, datetime
from typing import List, Dict

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

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from src.infrastructure.database.connection import get_db_connection, DatabaseConnection
from src.infrastructure.repositories.stock.sqlite_stock_repository import SqliteStockRepository
from src.infrastructure.repositories.preset.seed_condition_preset_repository import SeedConditionPresetRepository
from src.infrastructure.repositories.preset.redetection_condition_preset_repository import RedetectionConditionPresetRepository
from src.infrastructure.repositories.detection.block1_repository import Block1Repository
from src.infrastructure.repositories.detection.block2_repository import Block2Repository
from src.infrastructure.repositories.detection.block3_repository import Block3Repository
from src.infrastructure.repositories.detection.block4_repository import Block4Repository
from src.application.use_cases.pattern_detection.detect_patterns import DetectPatternsUseCase

console = Console()


def create_pattern_tree(pattern: Dict, pattern_num: int, block1_repo, block2_repo, block3_repo, block4_repo) -> Tree:
    """패턴 정보를 트리 형태로 생성"""
    tree = Tree(f"[bold cyan]Pattern #{pattern_num}[/bold cyan]")

    # Pattern ID 추출 (모든 블록에서 사용)
    pattern_id = pattern.get('pattern_id')

    # Block1 Seed
    block1_seed = pattern.get('seed_block1')
    if block1_seed:
        b1_info = f"[yellow]Block1 Seed[/yellow]: {block1_seed.started_at} ~ {block1_seed.ended_at or '진행중'}"
        b1_branch = tree.add(b1_info)
        b1_branch.add(f"진입가: {block1_seed.entry_close:,.0f}원")

        if hasattr(block1_seed, 'peak_price') and block1_seed.peak_price:
            gain = (block1_seed.peak_price - block1_seed.entry_close) / block1_seed.entry_close * 100
            b1_branch.add(f"최고가: {block1_seed.peak_price:,.0f}원 ([green]+{gain:.1f}%[/green])")

        # Block1 재탐지 상세
        if pattern_id:
            block1_redetections = block1_repo.find_by_pattern_and_condition(pattern_id, 'redetection')
            if block1_redetections:
                redetect_branch = b1_branch.add(f"Block1 재탐지: [cyan]{len(block1_redetections)}개[/cyan]")
                for idx, redetection in enumerate(block1_redetections, 1):
                    # 수익률 계산
                    gain_str = ""
                    if hasattr(redetection, 'peak_price') and redetection.peak_price and redetection.entry_close:
                        gain = (redetection.peak_price - redetection.entry_close) / redetection.entry_close * 100
                        gain_str = f" ([green]+{gain:.1f}%[/green])"

                    # 상세 정보
                    detail = (
                        f"[{idx}] {redetection.started_at} ~ {redetection.ended_at or '진행중'} | "
                        f"{redetection.entry_close:,.0f}원"
                    )
                    if hasattr(redetection, 'peak_price') and redetection.peak_price:
                        detail += f" → {redetection.peak_price:,.0f}원{gain_str}"

                    redetect_branch.add(detail)
            else:
                b1_branch.add(f"Block1 재탐지: [cyan]0개[/cyan]")

    # Block2 Seed
    block2_seed = pattern.get('seed_block2')
    if block2_seed:
        b2_info = f"[yellow]Block2 Seed[/yellow]: {block2_seed.started_at} ~ {block2_seed.ended_at or '진행중'}"
        b2_branch = tree.add(b2_info)
        b2_branch.add(f"진입가: {block2_seed.entry_close:,.0f}원")

        if hasattr(block2_seed, 'peak_price') and block2_seed.peak_price:
            gain = (block2_seed.peak_price - block2_seed.entry_close) / block2_seed.entry_close * 100
            b2_branch.add(f"최고가: {block2_seed.peak_price:,.0f}원 ([green]+{gain:.1f}%[/green])")

        # Block2 재탐지 상세
        if pattern_id:
            block2_redetections = block2_repo.find_by_pattern_and_condition(pattern_id, 'redetection')
            if block2_redetections:
                redetect_branch = b2_branch.add(f"Block2 재탐지: [cyan]{len(block2_redetections)}개[/cyan]")
                for idx, redetection in enumerate(block2_redetections, 1):
                    # 수익률 계산
                    gain_str = ""
                    if hasattr(redetection, 'peak_price') and redetection.peak_price and redetection.entry_close:
                        gain = (redetection.peak_price - redetection.entry_close) / redetection.entry_close * 100
                        gain_str = f" ([green]+{gain:.1f}%[/green])"

                    # 상세 정보
                    detail = (
                        f"[{idx}] {redetection.started_at} ~ {redetection.ended_at or '진행중'} | "
                        f"{redetection.entry_close:,.0f}원"
                    )
                    if hasattr(redetection, 'peak_price') and redetection.peak_price:
                        detail += f" → {redetection.peak_price:,.0f}원{gain_str}"

                    redetect_branch.add(detail)
            else:
                b2_branch.add(f"Block2 재탐지: [cyan]0개[/cyan]")

    # Block3 Seed
    block3_seed = pattern.get('seed_block3')
    if block3_seed:
        b3_info = f"[yellow]Block3 Seed[/yellow]: {block3_seed.started_at} ~ {block3_seed.ended_at or '진행중'}"
        b3_branch = tree.add(b3_info)
        b3_branch.add(f"진입가: {block3_seed.entry_close:,.0f}원")

        if hasattr(block3_seed, 'peak_price') and block3_seed.peak_price:
            gain = (block3_seed.peak_price - block3_seed.entry_close) / block3_seed.entry_close * 100
            b3_branch.add(f"최고가: {block3_seed.peak_price:,.0f}원 ([green]+{gain:.1f}%[/green])")

        # Block3 재탐지 상세
        if pattern_id:
            block3_redetections = block3_repo.find_by_pattern_and_condition(pattern_id, 'redetection')
            if block3_redetections:
                redetect_branch = b3_branch.add(f"Block3 재탐지: [cyan]{len(block3_redetections)}개[/cyan]")
                for idx, redetection in enumerate(block3_redetections, 1):
                    # 수익률 계산
                    gain_str = ""
                    if hasattr(redetection, 'peak_price') and redetection.peak_price and redetection.entry_close:
                        gain = (redetection.peak_price - redetection.entry_close) / redetection.entry_close * 100
                        gain_str = f" ([green]+{gain:.1f}%[/green])"

                    # 상세 정보
                    detail = (
                        f"[{idx}] {redetection.started_at} ~ {redetection.ended_at or '진행중'} | "
                        f"{redetection.entry_close:,.0f}원"
                    )
                    if hasattr(redetection, 'peak_price') and redetection.peak_price:
                        detail += f" → {redetection.peak_price:,.0f}원{gain_str}"

                    redetect_branch.add(detail)
            else:
                b3_branch.add(f"Block3 재탐지: [cyan]0개[/cyan]")

    # Block4 Seed (있으면)
    block4_seed = pattern.get('seed_block4')
    if block4_seed:
        b4_info = f"[yellow]Block4 Seed[/yellow]: {block4_seed.started_at} ~ {block4_seed.ended_at or '진행중'}"
        b4_branch = tree.add(b4_info)
        b4_branch.add(f"진입가: {block4_seed.entry_close:,.0f}원")

        if hasattr(block4_seed, 'peak_price') and block4_seed.peak_price:
            gain = (block4_seed.peak_price - block4_seed.entry_close) / block4_seed.entry_close * 100
            b4_branch.add(f"최고가: {block4_seed.peak_price:,.0f}원 ([green]+{gain:.1f}%[/green])")

        # Block4 재탐지 상세
        if pattern_id:
            block4_redetections = block4_repo.find_by_pattern_and_condition(pattern_id, 'redetection')
            if block4_redetections:
                redetect_branch = b4_branch.add(f"Block4 재탐지: [cyan]{len(block4_redetections)}개[/cyan]")
                for idx, redetection in enumerate(block4_redetections, 1):
                    # 수익률 계산
                    gain_str = ""
                    if hasattr(redetection, 'peak_price') and redetection.peak_price and redetection.entry_close:
                        gain = (redetection.peak_price - redetection.entry_close) / redetection.entry_close * 100
                        gain_str = f" ([green]+{gain:.1f}%[/green])"

                    # 상세 정보
                    detail = (
                        f"[{idx}] {redetection.started_at} ~ {redetection.ended_at or '진행중'} | "
                        f"{redetection.entry_close:,.0f}원"
                    )
                    if hasattr(redetection, 'peak_price') and redetection.peak_price:
                        detail += f" → {redetection.peak_price:,.0f}원{gain_str}"

                    redetect_branch.add(detail)
            else:
                b4_branch.add(f"Block4 재탐지: [cyan]0개[/cyan]")

    return tree


def create_summary_table(patterns: List[Dict], total_stats: Dict) -> Table:
    """패턴 요약 테이블 생성"""
    table = Table(title="패턴 탐지 요약", show_header=True, header_style="bold cyan")
    table.add_column("항목", style="cyan", width=20)
    table.add_column("값", style="green", width=30)

    table.add_row("총 패턴 수", f"{len(patterns)}개")
    table.add_row("Block1 재탐지", f"{total_stats.get('block1_redetections', 0)}개")
    table.add_row("Block2 재탐지", f"{total_stats.get('block2_redetections', 0)}개")
    table.add_row("Block3 재탐지", f"{total_stats.get('block3_redetections', 0)}개")
    table.add_row("Block4 재탐지", f"{total_stats.get('block4_redetections', 0)}개")

    total_redetections = (
        total_stats.get('block1_redetections', 0) +
        total_stats.get('block2_redetections', 0) +
        total_stats.get('block3_redetections', 0) +
        total_stats.get('block4_redetections', 0)
    )
    table.add_row("총 재탐지", f"[bold]{total_redetections}개[/bold]")

    return table


def detect_patterns_for_ticker(
    ticker: str,
    db: DatabaseConnection,
    stock_repo: SqliteStockRepository,
    seed_repo: SeedConditionPresetRepository,
    redetect_repo: RedetectionConditionPresetRepository,
    fromdate: date = None,
    todate: date = None,
    seed_preset: str = 'default_seed',
    redetect_preset: str = 'default_redetect',
    dry_run: bool = False,
    verbose: bool = False
) -> Dict:
    """
    단일 종목에 대한 패턴 탐지 실행

    Args:
        ticker: 종목 코드
        db: 데이터베이스 연결
        stock_repo: 주식 데이터 Repository
        seed_repo: Seed 조건 프리셋 Repository
        redetect_repo: 재탐지 조건 프리셋 Repository
        fromdate: 시작 날짜 (None이면 전체)
        todate: 종료 날짜 (None이면 전체)
        seed_preset: Seed 프리셋 이름
        redetect_preset: 재탐지 프리셋 이름
        dry_run: True면 데이터베이스에 저장 안 함
        verbose: 상세 출력 여부

    Returns:
        탐지 결과 딕셔너리
    """
    console.print(f"\n[bold cyan]{'=' * 80}[/bold cyan]")
    console.print(f"[bold cyan]종목 {ticker} 패턴 탐지[/bold cyan]")
    console.print(f"[bold cyan]{'=' * 80}[/bold cyan]\n")

    # 1. 데이터 로드
    console.print("[cyan]1. 종목 데이터 로드...[/cyan]")

    # 날짜 범위 자동 감지
    if fromdate is None or todate is None:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"   {ticker} 데이터 조회 중...", total=None)

            # 전체 데이터 로드 (날짜 자동 감지)
            stocks = stock_repo.get_stock_data(ticker, date(2015, 1, 1), date.today())

            if stocks:
                actual_fromdate = stocks[0].date
                actual_todate = stocks[-1].date
                console.print(f"   [green]OK[/green] {ticker}: {len(stocks):,}건 ({actual_fromdate} ~ {actual_todate})")
            else:
                console.print(f"   [red]ERROR[/red] {ticker}: 데이터 없음")
                return None
    else:
        stocks = stock_repo.get_stock_data(ticker, fromdate, todate)
        console.print(f"   [green]OK[/green] {ticker}: {len(stocks):,}건 ({fromdate} ~ {todate})")

    if not stocks:
        console.print(f"   [yellow]WARNING[/yellow] {ticker}: 수집된 데이터가 없습니다.\n")
        return None

    # 2. 프리셋 로드
    console.print(f"\n[cyan]2. 프리셋 로드...[/cyan]")
    seed_condition = seed_repo.load(seed_preset)
    redetect_condition = redetect_repo.load(redetect_preset)

    if not seed_condition or not redetect_condition:
        console.print(f"   [red]ERROR[/red] 프리셋을 찾을 수 없습니다.")
        console.print(f"   - Seed: {seed_preset}")
        console.print(f"   - Redetect: {redetect_preset}\n")
        return None

    console.print(f"   [green]OK[/green] Seed 조건: {seed_preset}")
    console.print(f"   [green]OK[/green] 재탐지 조건: {redetect_preset}")

    # 3. 패턴 탐지 실행
    console.print(f"\n[cyan]3. 패턴 탐지 실행...[/cyan]")
    console.print(f"   (Block1/2/3/4 Seed + 5년 재탐지)\n")

    use_case = DetectPatternsUseCase(db)

    # DetectPatternsUseCase의 출력을 캡처
    import io
    from contextlib import redirect_stdout

    if not verbose:
        # verbose 모드가 아니면 Use Case 출력 숨기기
        f = io.StringIO()
        with redirect_stdout(f):
            result = use_case.execute(
                ticker=ticker,
                stocks=stocks,
                seed_condition=seed_condition,
                redetection_condition=redetect_condition
            )
    else:
        # verbose 모드면 모든 출력 표시
        result = use_case.execute(
            ticker=ticker,
            stocks=stocks,
            seed_condition=seed_condition,
            redetection_condition=redetect_condition
        )

    return result


def main():
    """CLI 진입점"""
    parser = argparse.ArgumentParser(
        description="블록 패턴 탐지 스크립트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 기본: 아난티(025980) 전체 기간 탐지
  uv run python scripts/detect_patterns.py --ticker 025980

  # 다중 종목
  uv run python scripts/detect_patterns.py --ticker 025980,005930,035720

  # 기간 지정
  uv run python scripts/detect_patterns.py --ticker 025980 --from-date 2020-01-01

  # 다른 프리셋 사용
  uv run python scripts/detect_patterns.py --ticker 025980 --seed-preset strict_seed

  # 상세 출력
  uv run python scripts/detect_patterns.py --ticker 025980 --verbose

  # 미리보기만 (저장 안 함)
  uv run python scripts/detect_patterns.py --ticker 025980 --dry-run
        """
    )

    parser.add_argument(
        "--ticker",
        type=str,
        required=True,
        help="종목 코드 (예: 025980) 또는 쉼표로 구분된 여러 종목 (예: 025980,005930)"
    )

    parser.add_argument(
        "--from-date",
        type=str,
        default=None,
        help="시작 날짜 (YYYY-MM-DD, 기본값: DB의 최초 날짜)"
    )

    parser.add_argument(
        "--to-date",
        type=str,
        default=None,
        help="종료 날짜 (YYYY-MM-DD, 기본값: DB의 최신 날짜)"
    )

    parser.add_argument(
        "--seed-preset",
        type=str,
        default="default_seed",
        help="Seed 조건 프리셋 이름 (기본값: default_seed)"
    )

    parser.add_argument(
        "--redetect-preset",
        type=str,
        default="default_redetect",
        help="재탐지 조건 프리셋 이름 (기본값: default_redetect)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="데이터베이스에 저장하지 않고 미리보기만 (현재 미구현)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="상세 출력 모드 (Use Case 내부 로그 표시)"
    )

    parser.add_argument(
        "--db",
        type=str,
        default="data/database/stock_data.db",
        help="데이터베이스 파일 경로 (기본값: data/database/stock_data.db)"
    )

    args = parser.parse_args()

    # 날짜 파싱
    fromdate = None
    todate = None

    if args.from_date:
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

    # 종목 코드 파싱 (쉼표로 구분)
    tickers = [t.strip() for t in args.ticker.split(',')]

    console.print("\n" + "=" * 80)
    console.print("[bold cyan]블록 패턴 탐지 시작[/bold cyan]")
    console.print("=" * 80 + "\n")

    # DB 연결
    console.print("[cyan]데이터베이스 연결...[/cyan]")
    db = get_db_connection(args.db)
    console.print(f"   [green]OK[/green] DB 연결 완료: {args.db}\n")

    # Repository 초기화
    stock_repo = SqliteStockRepository(args.db)
    seed_repo = SeedConditionPresetRepository(db)
    redetect_repo = RedetectionConditionPresetRepository(db)
    block1_repo = Block1Repository(db)
    block2_repo = Block2Repository(db)
    block3_repo = Block3Repository(db)
    block4_repo = Block4Repository(db)

    # 각 종목별로 탐지 실행
    all_results = {}

    for ticker in tickers:
        try:
            result = detect_patterns_for_ticker(
                ticker=ticker,
                db=db,
                stock_repo=stock_repo,
                seed_repo=seed_repo,
                redetect_repo=redetect_repo,
                fromdate=fromdate,
                todate=todate,
                seed_preset=args.seed_preset,
                redetect_preset=args.redetect_preset,
                dry_run=args.dry_run,
                verbose=args.verbose
            )

            if result:
                all_results[ticker] = result

        except KeyboardInterrupt:
            console.print("\n[yellow]사용자에 의해 중단되었습니다.[/yellow]")
            sys.exit(130)

        except Exception as e:
            console.print(f"\n[red]{ticker} 탐지 중 에러 발생:[/red] {e}")
            if args.verbose:
                import traceback
                console.print(traceback.format_exc())
            continue

    # 결과 출력
    console.print("\n" + "=" * 80)
    console.print("[bold cyan]탐지 결과[/bold cyan]")
    console.print("=" * 80 + "\n")

    if not all_results:
        console.print("[yellow]탐지된 패턴이 없습니다.[/yellow]")
        return

    # 각 종목별 결과 출력
    for ticker, result in all_results.items():
        patterns = result.get('patterns', [])
        total_stats = result.get('total_stats', {})

        if not patterns:
            console.print(f"[yellow]{ticker}: 탐지된 패턴 없음[/yellow]\n")
            continue

        # 요약 테이블
        summary_table = create_summary_table(patterns, total_stats)
        console.print(summary_table)
        console.print()

        # 각 패턴 상세
        for idx, pattern in enumerate(patterns, 1):
            pattern_tree = create_pattern_tree(
                pattern, idx, block1_repo, block2_repo, block3_repo, block4_repo
            )
            console.print(pattern_tree)
            console.print()

    # 최종 요약
    total_patterns = sum(len(r.get('patterns', [])) for r in all_results.values())

    console.print("=" * 80)
    console.print(Panel(
        f"[bold green]탐지 완료![/bold green]\n"
        f"종목 수: {len(all_results)}개\n"
        f"총 패턴: {total_patterns}개",
        title="완료",
        border_style="green"
    ))


if __name__ == "__main__":
    main()
