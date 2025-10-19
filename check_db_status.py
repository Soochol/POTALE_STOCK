"""
데이터베이스 상태 확인 스크립트
Phase 1 Day 1: 데이터베이스 기본 통계 및 품질 검증
"""
import sys
from pathlib import Path
from datetime import date

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.infrastructure.database.connection import get_db_session
from src.infrastructure.database.models import StockInfo, StockPrice
from sqlalchemy import func, and_
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def check_database_status():
    """데이터베이스 전체 상태 확인"""

    console.print(Panel.fit(
        "[bold cyan]POTALE Stock Database Status Check[/bold cyan]",
        border_style="cyan"
    ))

    db_path = "data/database/stock_data.db"

    # 파일 존재 확인
    db_file = Path(db_path)
    if not db_file.exists():
        console.print(f"[red][X][/red] 데이터베이스 파일이 없습니다: {db_path}")
        return False

    file_size_mb = db_file.stat().st_size / (1024 * 1024)
    console.print(f"[green][OK][/green] 데이터베이스 파일: {db_path}")
    console.print(f"[green][OK][/green] 파일 크기: {file_size_mb:.2f} MB\n")

    try:
        with get_db_session(db_path) as session:
            # 1. 종목 정보 통계
            console.print("[bold]1. 종목 정보 (StockInfo)[/bold]")

            total_stocks = session.query(func.count(StockInfo.ticker)).scalar()
            kospi_count = session.query(func.count(StockInfo.ticker)).filter(
                StockInfo.market == 'KOSPI'
            ).scalar()
            kosdaq_count = session.query(func.count(StockInfo.ticker)).filter(
                StockInfo.market == 'KOSDAQ'
            ).scalar()

            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("항목", style="cyan")
            table.add_column("값", justify="right", style="green")

            table.add_row("총 종목 수", f"{total_stocks:,}개")
            table.add_row("KOSPI", f"{kospi_count:,}개")
            table.add_row("KOSDAQ", f"{kosdaq_count:,}개")

            console.print(table)
            console.print()

            # 2. 주가 데이터 통계
            console.print("[bold]2. 주가 데이터 (StockPrice)[/bold]")

            total_prices = session.query(func.count(StockPrice.id)).scalar()

            # 날짜 범위
            date_range = session.query(
                func.min(StockPrice.date).label('min_date'),
                func.max(StockPrice.date).label('max_date')
            ).first()

            # 데이터 있는 종목 수
            stocks_with_data = session.query(
                func.count(func.distinct(StockPrice.ticker))
            ).scalar()

            table2 = Table(show_header=True, header_style="bold magenta")
            table2.add_column("항목", style="cyan")
            table2.add_column("값", justify="right", style="green")

            table2.add_row("총 데이터 건수", f"{total_prices:,}건")
            table2.add_row("데이터 있는 종목", f"{stocks_with_data:,}개")
            table2.add_row("데이터 없는 종목", f"{total_stocks - stocks_with_data:,}개")

            if date_range.min_date and date_range.max_date:
                table2.add_row("날짜 범위 (최소)", str(date_range.min_date))
                table2.add_row("날짜 범위 (최대)", str(date_range.max_date))
                days_span = (date_range.max_date - date_range.min_date).days
                table2.add_row("전체 기간", f"{days_span:,}일")

            console.print(table2)
            console.print()

            # 3. 샘플 종목 확인 (삼성전자)
            console.print("[bold]3. 샘플 종목 확인 (삼성전자 005930)[/bold]")

            samsung_data_count = session.query(func.count(StockPrice.id)).filter(
                StockPrice.ticker == '005930'
            ).scalar()

            samsung_date_range = session.query(
                func.min(StockPrice.date).label('min_date'),
                func.max(StockPrice.date).label('max_date')
            ).filter(
                StockPrice.ticker == '005930'
            ).first()

            if samsung_data_count > 0:
                console.print(f"[green][OK][/green] 삼성전자 데이터: {samsung_data_count:,}건")
                console.print(f"[green][OK][/green] 기간: {samsung_date_range.min_date} ~ {samsung_date_range.max_date}")

                # 최근 5일 데이터 샘플
                recent_data = session.query(StockPrice).filter(
                    StockPrice.ticker == '005930'
                ).order_by(StockPrice.date.desc()).limit(5).all()

                if recent_data:
                    console.print("\n[bold]최근 5일 데이터 샘플:[/bold]")
                    sample_table = Table(show_header=True, header_style="bold magenta")
                    sample_table.add_column("날짜", style="cyan")
                    sample_table.add_column("시가", justify="right")
                    sample_table.add_column("고가", justify="right")
                    sample_table.add_column("저가", justify="right")
                    sample_table.add_column("종가", justify="right", style="green")
                    sample_table.add_column("거래량", justify="right")

                    for row in reversed(recent_data):
                        sample_table.add_row(
                            str(row.date),
                            f"{row.open:,.0f}" if row.open else "N/A",
                            f"{row.high:,.0f}" if row.high else "N/A",
                            f"{row.low:,.0f}" if row.low else "N/A",
                            f"{row.close:,.0f}" if row.close else "N/A",
                            f"{row.volume:,}" if row.volume else "N/A"
                        )

                    console.print(sample_table)
            else:
                console.print(f"[yellow]![/yellow] 삼성전자 데이터 없음")

            console.print()

            # 4. 데이터 품질 기본 체크
            console.print("[bold]4. 데이터 품질 기본 체크[/bold]")

            # NULL 체크
            null_open = session.query(func.count(StockPrice.id)).filter(
                StockPrice.open.is_(None)
            ).scalar()
            null_high = session.query(func.count(StockPrice.id)).filter(
                StockPrice.high.is_(None)
            ).scalar()
            null_low = session.query(func.count(StockPrice.id)).filter(
                StockPrice.low.is_(None)
            ).scalar()
            null_close = session.query(func.count(StockPrice.id)).filter(
                StockPrice.close.is_(None)
            ).scalar()
            null_volume = session.query(func.count(StockPrice.id)).filter(
                StockPrice.volume.is_(None)
            ).scalar()

            total_nulls = null_open + null_high + null_low + null_close + null_volume

            quality_table = Table(show_header=True, header_style="bold magenta")
            quality_table.add_column("검사 항목", style="cyan")
            quality_table.add_column("결과", justify="right")
            quality_table.add_column("상태", justify="center")

            quality_table.add_row(
                "NULL 데이터 (open)",
                f"{null_open:,}건",
                "[green]OK[/green]" if null_open == 0 else "[red]FAIL[/red]"
            )
            quality_table.add_row(
                "NULL 데이터 (high)",
                f"{null_high:,}건",
                "[green]OK[/green]" if null_high == 0 else "[red]FAIL[/red]"
            )
            quality_table.add_row(
                "NULL 데이터 (low)",
                f"{null_low:,}건",
                "[green]OK[/green]" if null_low == 0 else "[red]FAIL[/red]"
            )
            quality_table.add_row(
                "NULL 데이터 (close)",
                f"{null_close:,}건",
                "[green]OK[/green]" if null_close == 0 else "[red]FAIL[/red]"
            )
            quality_table.add_row(
                "NULL 데이터 (volume)",
                f"{null_volume:,}건",
                "[green]OK[/green]" if null_volume == 0 else "[red]FAIL[/red]"
            )

            console.print(quality_table)
            console.print()

            # 요약
            console.print(Panel.fit(
                f"[bold]총 {total_nulls:,}건의 NULL 데이터 발견[/bold]",
                border_style="yellow" if total_nulls > 0 else "green"
            ))

            return True

    except Exception as e:
        console.print(f"[red]✗[/red] 데이터베이스 조회 실패: {e}")
        import traceback
        console.print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = check_database_status()
    sys.exit(0 if success else 1)
