"""
아난티(025980) 데이터 수집 스크립트
2015-01-01 ~ 오늘까지
"""
import sys
from pathlib import Path
from datetime import date

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.infrastructure.collectors.naver.naver_hybrid_collector import NaverHybridCollector
from src.infrastructure.repositories.sqlite_stock_repository import SqliteStockRepository
from src.infrastructure.database.connection import DatabaseConnection
from src.infrastructure.database.models import StockInfo
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

console = Console()

def collect_ananti():
    """아난티 데이터 수집"""

    ticker = "025980"
    name = "아난티"
    start_date = date(2015, 1, 1)
    end_date = date.today()

    console.print(f"\n[bold cyan]아난티({ticker}) 데이터 수집[/bold cyan]")
    console.print(f"기간: {start_date} ~ {end_date}\n")

    # DB 연결
    db_path = "data/database/stock_data.db"
    db_conn = DatabaseConnection(db_path)

    # Repository 초기화
    stock_repo = SqliteStockRepository(db_path)

    # 1. 종목 정보 등록
    console.print("[1/3] 종목 정보 등록...")

    try:
        session = db_conn.get_session()

        # 기존 종목 확인
        existing = session.query(StockInfo).filter(StockInfo.ticker == ticker).first()

        if existing:
            console.print(f"[yellow]종목 정보 이미 존재: {existing.ticker} {existing.name}[/yellow]")
        else:
            stock_info = StockInfo(
                ticker=ticker,
                name=name,
                market="KOSDAQ"
            )
            session.add(stock_info)
            session.commit()
            console.print(f"[green]종목 정보 등록 완료: {ticker} {name}[/green]")

        session.close()

    except Exception as e:
        console.print(f"[red]종목 정보 등록 실패: {e}[/red]")
        return False

    # 2. 주가 데이터 수집
    console.print("\n[2/3] 주가 데이터 수집 (NaverHybridCollector)...")

    try:
        collector = NaverHybridCollector()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task(f"수집 중: {ticker} {name}", total=None)

            stocks = collector.collect_period(
                ticker=ticker,
                name=name,
                start_date=start_date,
                end_date=end_date
            )

            progress.update(task, completed=True)

        if not stocks:
            console.print("[yellow]수집된 데이터가 없습니다[/yellow]")
            return False

        console.print(f"[green]수집 완료: {len(stocks)}건[/green]")

    except Exception as e:
        console.print(f"[red]데이터 수집 실패: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())
        return False

    # 3. DB 저장
    console.print("\n[3/3] 데이터베이스 저장...")

    try:
        success = stock_repo.save_stock_data(stocks)

        if success:
            console.print(f"[green]저장 완료: {len(stocks)}건[/green]")
        else:
            console.print("[yellow]저장 중 일부 오류 발생[/yellow]")

    except Exception as e:
        console.print(f"[red]데이터 저장 실패: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())
        return False

    # 4. 저장 확인
    console.print("\n[확인] 저장된 데이터 조회...")

    try:
        saved_stocks = stock_repo.get_stock_data(ticker, start_date, end_date)
        console.print(f"[green]DB 조회 성공: {len(saved_stocks)}건[/green]")

        if saved_stocks:
            # 샘플 데이터 출력 (최근 5개)
            console.print("\n[bold]최근 5일 데이터 샘플:[/bold]")
            from rich.table import Table

            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("날짜", style="cyan")
            table.add_column("시가", justify="right")
            table.add_column("고가", justify="right")
            table.add_column("저가", justify="right")
            table.add_column("종가", justify="right", style="green")
            table.add_column("거래량", justify="right")

            for stock in saved_stocks[-5:]:
                table.add_row(
                    str(stock.date),
                    f"{stock.open:,.0f}",
                    f"{stock.high:,.0f}",
                    f"{stock.low:,.0f}",
                    f"{stock.close:,.0f}",
                    f"{stock.volume:,}"
                )

            console.print(table)

        return True

    except Exception as e:
        console.print(f"[red]데이터 조회 실패: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())
        return False

if __name__ == "__main__":
    console.print("\n" + "="*60)
    console.print("[bold cyan]POTALE - 아난티 데이터 수집 스크립트[/bold cyan]")
    console.print("="*60)

    success = collect_ananti()

    console.print("\n" + "="*60)
    if success:
        console.print("[bold green]수집 완료![/bold green]")
        console.print("="*60 + "\n")
        sys.exit(0)
    else:
        console.print("[bold red]수집 실패[/bold red]")
        console.print("="*60 + "\n")
        sys.exit(1)
