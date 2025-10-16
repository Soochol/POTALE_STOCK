"""
Trainer - 주식 데이터 학습 관리
"""
import numpy as np
import pandas as pd
from typing import List, Optional, Tuple
from pathlib import Path
from rich.console import Console
from rich.table import Table

from ..domain.entities.stock import Stock
from .models import StockPredictionModel, SimpleClassificationModel

console = Console()


class StockTrainer:
    """주식 데이터 학습 관리 클래스"""

    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.console = Console()

    def stocks_to_dataframe(self, stocks: List[Stock]) -> pd.DataFrame:
        """Stock 리스트를 DataFrame으로 변환"""
        data = {
            'date': [s.date for s in stocks],
            'ticker': [s.ticker for s in stocks],
            'open': [s.open for s in stocks],
            'high': [s.high for s in stocks],
            'low': [s.low for s in stocks],
            'close': [s.close for s in stocks],
            'volume': [s.volume for s in stocks],
        }
        df = pd.DataFrame(data)
        df = df.sort_values(['ticker', 'date'])
        return df

    def prepare_lstm_data(
        self,
        stocks: List[Stock],
        ticker: str
    ) -> Optional[np.ndarray]:
        """
        LSTM 학습용 데이터 준비

        Args:
            stocks: 주식 데이터 리스트
            ticker: 종목 코드

        Returns:
            OHLCV 데이터 배열 (N, 5)
        """
        df = self.stocks_to_dataframe(stocks)

        # 특정 종목만 필터링
        ticker_df = df[df['ticker'] == ticker].copy()

        if ticker_df.empty:
            console.print(f"[red]✗[/red] {ticker} 데이터가 없습니다.")
            return None

        # OHLCV 데이터 추출
        data = ticker_df[['open', 'high', 'low', 'close', 'volume']].values

        if len(data) < 100:
            console.print(f"[yellow]![/yellow] {ticker} 데이터가 부족합니다 (최소 100일 필요)")
            return None

        return data

    def train_lstm_model(
        self,
        stocks: List[Stock],
        ticker: str,
        sequence_length: int = 60,
        epochs: int = 50,
        batch_size: int = 32,
        save_model: bool = True
    ) -> Optional[StockPredictionModel]:
        """
        LSTM 모델 학습

        Args:
            stocks: 주식 데이터 리스트
            ticker: 종목 코드
            sequence_length: 시퀀스 길이
            epochs: 에포크 수
            batch_size: 배치 크기
            save_model: 모델 저장 여부

        Returns:
            학습된 모델
        """
        console.print(f"\n[cyan]{'='*60}[/cyan]")
        console.print(f"[bold cyan]{ticker} LSTM 모델 학습 시작[/bold cyan]")
        console.print(f"[cyan]{'='*60}[/cyan]\n")

        # 데이터 준비
        data = self.prepare_lstm_data(stocks, ticker)
        if data is None:
            return None

        # 모델 생성
        model = StockPredictionModel(
            sequence_length=sequence_length,
            n_features=5  # OHLCV
        )

        # 데이터 전처리
        X_train, y_train, X_test, y_test = model.prepare_data(data)

        console.print(f"[green]✓[/green] 학습 데이터: {X_train.shape[0]}개")
        console.print(f"[green]✓[/green] 테스트 데이터: {X_test.shape[0]}개\n")

        # 학습
        console.print("[cyan]모델 학습 중...[/cyan]")
        history = model.train(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            verbose=1
        )

        # 평가
        loss, mae = model.evaluate(X_test, y_test)
        console.print(f"\n[green]✓[/green] 테스트 Loss: {loss:.4f}")
        console.print(f"[green]✓[/green] 테스트 MAE: {mae:.4f}")

        # 모델 저장
        if save_model:
            model_path = self.models_dir / f"{ticker}_lstm_model.h5"
            model.save(str(model_path))
            console.print(f"\n[green]✓[/green] 모델 저장: {model_path}")

        return model

    def prepare_classification_data(
        self,
        stocks: List[Stock]
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        분류 모델 학습용 데이터 준비

        Args:
            stocks: 주식 데이터 리스트

        Returns:
            (features_df, labels)
        """
        df = self.stocks_to_dataframe(stocks)

        # 기술적 지표 계산
        df = self._calculate_features(df)

        # 레이블 생성: 다음날 상승(1) / 하락(0)
        df['future_return'] = df.groupby('ticker')['close'].shift(-1) / df['close'] - 1
        df['label'] = (df['future_return'] > 0).astype(int)

        # NaN 제거
        df = df.dropna()

        # 특성과 레이블 분리
        feature_columns = [col for col in df.columns if col not in [
            'date', 'ticker', 'future_return', 'label'
        ]]
        X = df[feature_columns]
        y = df['label']

        return X, y

    def _calculate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """기술적 지표 특성 계산"""
        df = df.copy()

        # 그룹별로 계산 (종목별)
        for ticker in df['ticker'].unique():
            mask = df['ticker'] == ticker
            ticker_df = df[mask].copy()

            # 이동평균
            ticker_df['MA_5'] = ticker_df['close'].rolling(5).mean()
            ticker_df['MA_20'] = ticker_df['close'].rolling(20).mean()

            # RSI
            delta = ticker_df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            ticker_df['RSI'] = 100 - (100 / (1 + rs))

            # 거래량 변화
            ticker_df['volume_change'] = ticker_df['volume'].pct_change()

            # 가격 변화
            ticker_df['price_change'] = ticker_df['close'].pct_change()

            df.loc[mask] = ticker_df

        return df

    def train_classification_model(
        self,
        stocks: List[Stock],
        epochs: int = 50,
        batch_size: int = 32,
        save_model: bool = True
    ) -> Optional[SimpleClassificationModel]:
        """
        분류 모델 학습 (상승/하락 예측)

        Args:
            stocks: 주식 데이터 리스트
            epochs: 에포크 수
            batch_size: 배치 크기
            save_model: 모델 저장 여부

        Returns:
            학습된 모델
        """
        console.print(f"\n[cyan]{'='*60}[/cyan]")
        console.print(f"[bold cyan]분류 모델 학습 시작[/bold cyan]")
        console.print(f"[cyan]{'='*60}[/cyan]\n")

        # 데이터 준비
        X, y = self.prepare_classification_data(stocks)

        console.print(f"[green]✓[/green] 전체 데이터: {len(X)}개")
        console.print(f"[green]✓[/green] 특성 수: {X.shape[1]}개")
        console.print(f"[green]✓[/green] 상승 비율: {y.mean():.2%}\n")

        # 학습/테스트 분할
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        # 모델 생성
        model = SimpleClassificationModel(n_features=X.shape[1])

        # 학습
        console.print("[cyan]모델 학습 중...[/cyan]")
        history = model.train(
            X_train.values, y_train.values,
            epochs=epochs,
            batch_size=batch_size,
            verbose=1
        )

        # 평가
        loss, accuracy = model.evaluate(X_test.values, y_test.values)
        console.print(f"\n[green]✓[/green] 테스트 Loss: {loss:.4f}")
        console.print(f"[green]✓[/green] 테스트 Accuracy: {accuracy:.4f}")

        # 모델 저장
        if save_model:
            model_path = self.models_dir / "classification_model.h5"
            model.save(str(model_path))
            console.print(f"\n[green]✓[/green] 모델 저장: {model_path}")

        return model

    def list_models(self) -> None:
        """저장된 모델 목록 출력"""
        model_files = list(self.models_dir.glob("*.h5"))

        if not model_files:
            console.print("[yellow]![/yellow] 저장된 모델이 없습니다.")
            return

        table = Table(title="저장된 모델 목록")
        table.add_column("파일명", style="cyan")
        table.add_column("크기", justify="right", style="green")

        for model_file in model_files:
            size = model_file.stat().st_size / 1024  # KB
            table.add_row(
                model_file.name,
                f"{size:.2f} KB"
            )

        console.print(table)
