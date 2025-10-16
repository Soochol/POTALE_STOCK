"""
Main CLI Entry Point
"""
import click
from datetime import datetime, date, timedelta
from pathlib import Path

from src.infrastructure.repositories.pykrx_stock_repository import PyKrxStockRepository
from src.infrastructure.repositories.sqlite_stock_repository import SqliteStockRepository
from src.infrastructure.repositories.yaml_condition_repository import YamlConditionRepository
from src.infrastructure.collectors.stock_price_collector import StockPriceCollector
from src.infrastructure.collectors.market_info_collector import MarketInfoCollector
from src.application.use_cases.collect_stock_data import CollectStockDataUseCase
from src.application.use_cases.detect_condition import DetectConditionUseCase
from src.application.use_cases.manage_condition import (
    CreateConditionUseCase,
    UpdateConditionUseCase,
    DeleteConditionUseCase,
    ListConditionsUseCase
)
from src.application.services.indicator_calculator import IndicatorCalculator
from src.application.services.condition_checker import ConditionChecker
from src.domain.entities.condition import Rule, RuleType
from src.learning.trainer import StockTrainer

from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """
    주식 분석 및 AI 학습 CLI 프로그램

    한국 주식 시장 데이터를 수집하고 조건을 설정하여 탐지한 후 AI 학습을 수행합니다.
    """
    pass


@cli.group()
def collect():
    """데이터 수집 관련 명령어"""
    pass


@collect.command('stocks')
@click.option('--tickers', '-t', multiple=True, help='종목 코드 (여러 개 가능)')
@click.option('--market', '-m', type=click.Choice(['KOSPI', 'KOSDAQ', 'ALL']), default='KOSPI', help='시장 구분')
@click.option('--top-n', type=int, help='시가총액 상위 N개 종목')
@click.option('--start-date', '-s', help='시작일 (YYYY-MM-DD)')
@click.option('--end-date', '-e', help='종료일 (YYYY-MM-DD)')
def collect_stocks(tickers, market, top_n, start_date, end_date):
    """주식 가격 데이터 수집 (DB 저장)"""
    # 날짜 처리
    start = None
    end = None
    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d").date()

    # Collector 생성
    repository = SqliteStockRepository()
    collector = StockPriceCollector(repository)

    # 수집 실행
    if tickers:
        result = collector.collect(
            tickers=list(tickers),
            start_date=start,
            end_date=end
        )
    else:
        result = collector.collect(
            market=market,
            start_date=start,
            end_date=end,
            top_n=top_n
        )

    # 결과 출력
    if result.success:
        console.print(f"\n[green]✓[/green] 수집 완료!")
        console.print(f"  - 레코드 수: {result.record_count}개")
        if result.duration_seconds:
            console.print(f"  - 소요 시간: {result.duration_seconds:.1f}초")
    else:
        console.print(f"\n[red]✗[/red] 수집 실패: {result.error_message}")


@collect.command('info')
@click.option('--market', '-m', type=click.Choice(['KOSPI', 'KOSDAQ', 'ALL']), default='ALL', help='시장 구분')
@click.option('--include-market-cap', is_flag=True, help='시가총액 데이터 포함')
def collect_info(market, include_market_cap):
    """종목 정보 및 시가총액 데이터 수집"""
    repository = SqliteStockRepository()
    collector = MarketInfoCollector(repository)

    result = collector.collect(
        market=market,
        include_market_cap=include_market_cap
    )

    if result.success:
        console.print(f"\n[green]✓[/green] 수집 완료!")
        console.print(f"  - 레코드 수: {result.record_count}개")
    else:
        console.print(f"\n[red]✗[/red] 수집 실패: {result.error_message}")


@collect.command('update')
@click.option('--days', type=int, default=7, help='최근 N일 업데이트')
def update_recent(days):
    """최근 N일 데이터 업데이트"""
    repository = SqliteStockRepository()
    collector = StockPriceCollector(repository)

    result = collector.update_recent_data(days=days)

    if result.success:
        console.print(f"\n[green]✓[/green] 업데이트 완료!")
        console.print(f"  - 레코드 수: {result.record_count}개")
    else:
        console.print(f"\n[red]✗[/red] 업데이트 실패: {result.error_message}")


@cli.group()
def condition():
    """조건 관리 관련 명령어"""
    pass


@condition.command('list')
def list_conditions():
    """등록된 조건 목록 조회"""
    condition_repo = YamlConditionRepository()
    use_case = ListConditionsUseCase(condition_repo)

    conditions = use_case.execute()

    if not conditions:
        console.print("[yellow]![/yellow] 등록된 조건이 없습니다.")
        return

    table = Table(title="등록된 조건 목록")
    table.add_column("조건명", style="cyan", no_wrap=True)
    table.add_column("설명", style="white")
    table.add_column("규칙 수", justify="center", style="green")

    for cond in conditions:
        table.add_row(
            cond.name,
            cond.description,
            str(len(cond.rules))
        )

    console.print(table)


@condition.command('create')
@click.option('--name', '-n', required=True, help='조건 이름')
@click.option('--description', '-d', required=True, help='조건 설명')
def create_condition(name, description):
    """새로운 조건 생성 (대화형)"""
    console.print(f"\n[bold cyan]조건 생성: {name}[/bold cyan]\n")

    rules = []

    while True:
        console.print("\n규칙 유형을 선택하세요:")
        console.print("1. 골든크로스 (Cross Over)")
        console.print("2. 지표 임계값 (Indicator Threshold)")
        console.print("3. 거래량 증가 (Volume Increase)")
        console.print("4. 가격 변화 (Price Change)")
        console.print("0. 완료")

        choice = click.prompt("선택", type=int)

        if choice == 0:
            break
        elif choice == 1:
            indicator1 = click.prompt("단기 지표 (예: MA_5)", default="MA_5")
            indicator2 = click.prompt("장기 지표 (예: MA_20)", default="MA_20")
            rules.append(Rule(
                type=RuleType.CROSS_OVER,
                parameters={'indicator1': indicator1, 'indicator2': indicator2}
            ))
        elif choice == 2:
            indicator = click.prompt("지표 (예: RSI)", default="RSI")
            condition_op = click.prompt("조건 (>, <, >=, <=, ==)", default="<=")
            value = click.prompt("임계값", type=float)
            rules.append(Rule(
                type=RuleType.INDICATOR_THRESHOLD,
                parameters={'indicator': indicator, 'condition': condition_op, 'value': value}
            ))
        elif choice == 3:
            threshold = click.prompt("임계값 (예: 2.0 = 평균의 2배)", type=float, default=2.0)
            period = click.prompt("기간 (일)", type=int, default=20)
            rules.append(Rule(
                type=RuleType.VOLUME_INCREASE,
                parameters={'threshold': threshold, 'period': period}
            ))
        elif choice == 4:
            days = click.prompt("기간 (일)", type=int, default=1)
            threshold = click.prompt("변화율 (예: 0.02 = 2%)", type=float, default=0.02)
            rules.append(Rule(
                type=RuleType.PRICE_CHANGE,
                parameters={'days': days, 'threshold': threshold}
            ))

    if not rules:
        console.print("[red]✗[/red] 최소 1개 이상의 규칙이 필요합니다.")
        return

    # 조건 생성
    condition_repo = YamlConditionRepository()
    use_case = CreateConditionUseCase(condition_repo)

    try:
        cond = use_case.execute(name=name, description=description, rules=rules)
        console.print(f"\n[green]✓[/green] 조건 '{cond.name}' 생성 완료")
    except Exception as e:
        console.print(f"\n[red]✗[/red] 조건 생성 실패: {str(e)}")


@condition.command('delete')
@click.argument('name')
def delete_condition(name):
    """조건 삭제"""
    condition_repo = YamlConditionRepository()
    use_case = DeleteConditionUseCase(condition_repo)

    try:
        use_case.execute(name)
        console.print(f"[green]✓[/green] 조건 '{name}' 삭제 완료")
    except Exception as e:
        console.print(f"[red]✗[/red] {str(e)}")


@cli.command('detect')
@click.option('--condition-name', '-c', required=True, help='조건 이름')
@click.option('--tickers', '-t', multiple=True, help='종목 코드 (여러 개 가능)')
@click.option('--market', '-m', type=click.Choice(['KOSPI', 'KOSDAQ', 'ALL']), default='ALL', help='시장 구분')
@click.option('--top-n', type=int, default=100, help='시가총액 상위 N개 종목')
@click.option('--start-date', '-s', help='시작일 (YYYY-MM-DD)')
@click.option('--end-date', '-e', help='종료일 (YYYY-MM-DD)')
def detect(condition_name, tickers, market, top_n, start_date, end_date):
    """조건 탐지 실행"""
    console.print(f"\n[bold cyan]조건 탐지: {condition_name}[/bold cyan]\n")

    # 날짜 처리
    if not start_date:
        start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()

    # 데이터 수집
    stock_repo = PyKrxStockRepository()
    collect_use_case = CollectStockDataUseCase(stock_repo)

    if tickers:
        stocks = collect_use_case.execute(
            tickers=list(tickers),
            start_date=start,
            end_date=end,
            save=False
        )
    else:
        stocks = collect_use_case.execute_all_market(
            market=market,
            start_date=start,
            end_date=end,
            top_n=top_n
        )

    if not stocks:
        console.print("[red]✗[/red] 수집된 데이터가 없습니다.")
        return

    # 조건 탐지
    condition_repo = YamlConditionRepository()
    indicator_calc = IndicatorCalculator()
    condition_checker = ConditionChecker()

    detect_use_case = DetectConditionUseCase(
        condition_repo,
        indicator_calc,
        condition_checker
    )

    try:
        result = detect_use_case.execute(condition_name, stocks)

        console.print(f"\n[green]✓[/green] 탐지 완료: {result.count}개 종목")

        if result.count > 0:
            # 결과 출력
            table = Table(title=f"탐지 결과 - {condition_name}")
            table.add_column("종목코드", style="cyan")
            table.add_column("종목명", style="yellow")
            table.add_column("날짜", style="white")
            table.add_column("종가", justify="right", style="green")

            for stock in result.stocks[:20]:  # 상위 20개만
                table.add_row(
                    stock.ticker,
                    stock.name,
                    str(stock.date),
                    f"{stock.close:,.0f}"
                )

            console.print(table)

    except Exception as e:
        console.print(f"[red]✗[/red] 탐지 실패: {str(e)}")


@cli.group()
def train():
    """AI 학습 관련 명령어"""
    pass


@train.command('lstm')
@click.option('--ticker', '-t', required=True, help='종목 코드')
@click.option('--start-date', '-s', help='시작일 (YYYY-MM-DD)')
@click.option('--end-date', '-e', help='종료일 (YYYY-MM-DD)')
@click.option('--epochs', type=int, default=50, help='에포크 수')
@click.option('--batch-size', type=int, default=32, help='배치 크기')
def train_lstm(ticker, start_date, end_date, epochs, batch_size):
    """LSTM 모델 학습"""
    # 날짜 처리
    if not start_date:
        start_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")  # 2년
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()

    # 데이터 수집
    stock_repo = PyKrxStockRepository()
    collect_use_case = CollectStockDataUseCase(stock_repo)

    stocks = collect_use_case.execute(
        tickers=[ticker],
        start_date=start,
        end_date=end,
        save=False
    )

    if not stocks:
        console.print("[red]✗[/red] 데이터 수집 실패")
        return

    # 학습
    trainer = StockTrainer()
    model = trainer.train_lstm_model(
        stocks=stocks,
        ticker=ticker,
        epochs=epochs,
        batch_size=batch_size,
        save_model=True
    )

    if model:
        console.print(f"\n[green]✓[/green] 학습 완료!")


@train.command('classification')
@click.option('--market', '-m', type=click.Choice(['KOSPI', 'KOSDAQ', 'ALL']), default='KOSPI', help='시장 구분')
@click.option('--top-n', type=int, default=50, help='시가총액 상위 N개 종목')
@click.option('--start-date', '-s', help='시작일 (YYYY-MM-DD)')
@click.option('--end-date', '-e', help='종료일 (YYYY-MM-DD)')
@click.option('--epochs', type=int, default=50, help='에포크 수')
@click.option('--batch-size', type=int, default=32, help='배치 크기')
def train_classification(market, top_n, start_date, end_date, epochs, batch_size):
    """분류 모델 학습 (상승/하락 예측)"""
    # 날짜 처리
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")  # 1년
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()

    # 데이터 수집
    stock_repo = PyKrxStockRepository()
    collect_use_case = CollectStockDataUseCase(stock_repo)

    stocks = collect_use_case.execute_all_market(
        market=market,
        start_date=start,
        end_date=end,
        top_n=top_n
    )

    if not stocks:
        console.print("[red]✗[/red] 데이터 수집 실패")
        return

    # 학습
    trainer = StockTrainer()
    model = trainer.train_classification_model(
        stocks=stocks,
        epochs=epochs,
        batch_size=batch_size,
        save_model=True
    )

    if model:
        console.print(f"\n[green]✓[/green] 학습 완료!")


@train.command('list-models')
def list_models():
    """저장된 모델 목록"""
    trainer = StockTrainer()
    trainer.list_models()


if __name__ == '__main__':
    cli()
