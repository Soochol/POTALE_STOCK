"""
AI Models - 주식 예측 모델
"""
import numpy as np
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.preprocessing import MinMaxScaler
from typing import Tuple, Optional


class StockPredictionModel:
    """LSTM 기반 주식 예측 모델"""

    def __init__(
        self,
        sequence_length: int = 60,
        n_features: int = 5,
        lstm_units: int = 50,
        dropout: float = 0.2
    ):
        """
        Args:
            sequence_length: 입력 시퀀스 길이
            n_features: 입력 특성 수 (OHLCV = 5)
            lstm_units: LSTM 유닛 수
            dropout: 드롭아웃 비율
        """
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.lstm_units = lstm_units
        self.dropout = dropout
        self.model: Optional[keras.Model] = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))

    def build_model(self) -> keras.Model:
        """LSTM 모델 구축"""
        model = keras.Sequential([
            layers.LSTM(
                self.lstm_units,
                return_sequences=True,
                input_shape=(self.sequence_length, self.n_features)
            ),
            layers.Dropout(self.dropout),

            layers.LSTM(self.lstm_units, return_sequences=True),
            layers.Dropout(self.dropout),

            layers.LSTM(self.lstm_units),
            layers.Dropout(self.dropout),

            layers.Dense(25, activation='relu'),
            layers.Dense(1)
        ])

        model.compile(
            optimizer='adam',
            loss='mean_squared_error',
            metrics=['mae']
        )

        self.model = model
        return model

    def prepare_data(
        self,
        data: np.ndarray,
        train_split: float = 0.8
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        데이터 전처리 및 학습/테스트 분할

        Args:
            data: 원본 데이터 (N, features)
            train_split: 학습 데이터 비율

        Returns:
            X_train, y_train, X_test, y_test
        """
        # 데이터 정규화
        scaled_data = self.scaler.fit_transform(data)

        # 시퀀스 데이터 생성
        X, y = [], []
        for i in range(self.sequence_length, len(scaled_data)):
            X.append(scaled_data[i - self.sequence_length:i])
            y.append(scaled_data[i, 3])  # Close price (4번째 컬럼)

        X, y = np.array(X), np.array(y)

        # 학습/테스트 분할
        split_idx = int(len(X) * train_split)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        return X_train, y_train, X_test, y_test

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        epochs: int = 50,
        batch_size: int = 32,
        validation_split: float = 0.1,
        verbose: int = 1
    ) -> keras.callbacks.History:
        """
        모델 학습

        Args:
            X_train: 학습 데이터
            y_train: 학습 레이블
            epochs: 에포크 수
            batch_size: 배치 크기
            validation_split: 검증 데이터 비율
            verbose: 출력 레벨

        Returns:
            학습 히스토리
        """
        if self.model is None:
            self.build_model()

        # Early stopping 콜백
        early_stop = keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        )

        # 학습
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=[early_stop],
            verbose=verbose
        )

        return history

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        예측 수행

        Args:
            X: 입력 데이터

        Returns:
            예측값
        """
        if self.model is None:
            raise ValueError("모델이 학습되지 않았습니다.")

        predictions = self.model.predict(X)

        # 역정규화 (Close price만)
        # 원본 스케일러의 min/max 사용
        close_min = self.scaler.data_min_[3]
        close_max = self.scaler.data_max_[3]
        predictions_rescaled = predictions * (close_max - close_min) + close_min

        return predictions_rescaled

    def evaluate(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> Tuple[float, float]:
        """
        모델 평가

        Args:
            X_test: 테스트 데이터
            y_test: 테스트 레이블

        Returns:
            (loss, mae)
        """
        if self.model is None:
            raise ValueError("모델이 학습되지 않았습니다.")

        loss, mae = self.model.evaluate(X_test, y_test, verbose=0)
        return loss, mae

    def save(self, filepath: str) -> None:
        """모델 저장"""
        if self.model is None:
            raise ValueError("모델이 학습되지 않았습니다.")

        self.model.save(filepath)

    def load(self, filepath: str) -> None:
        """모델 로드"""
        self.model = keras.models.load_model(filepath)


class SimpleClassificationModel:
    """간단한 분류 모델 (상승/하락 예측)"""

    def __init__(self, n_features: int = 20):
        """
        Args:
            n_features: 입력 특성 수
        """
        self.n_features = n_features
        self.model: Optional[keras.Model] = None

    def build_model(self) -> keras.Model:
        """분류 모델 구축"""
        model = keras.Sequential([
            layers.Dense(64, activation='relu', input_shape=(self.n_features,)),
            layers.Dropout(0.3),
            layers.Dense(32, activation='relu'),
            layers.Dropout(0.3),
            layers.Dense(16, activation='relu'),
            layers.Dense(1, activation='sigmoid')  # 이진 분류
        ])

        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )

        self.model = model
        return model

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        epochs: int = 50,
        batch_size: int = 32,
        validation_split: float = 0.2,
        verbose: int = 1
    ) -> keras.callbacks.History:
        """모델 학습"""
        if self.model is None:
            self.build_model()

        early_stop = keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=5,
            restore_best_weights=True
        )

        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=[early_stop],
            verbose=verbose
        )

        return history

    def predict(self, X: np.ndarray) -> np.ndarray:
        """예측 수행 (확률)"""
        if self.model is None:
            raise ValueError("모델이 학습되지 않았습니다.")

        return self.model.predict(X)

    def predict_classes(self, X: np.ndarray) -> np.ndarray:
        """예측 수행 (클래스)"""
        probabilities = self.predict(X)
        return (probabilities > 0.5).astype(int)

    def evaluate(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> Tuple[float, float]:
        """모델 평가"""
        if self.model is None:
            raise ValueError("모델이 학습되지 않았습니다.")

        loss, accuracy = self.model.evaluate(X_test, y_test, verbose=0)
        return loss, accuracy

    def save(self, filepath: str) -> None:
        """모델 저장"""
        if self.model is None:
            raise ValueError("모델이 학습되지 않았습니다.")

        self.model.save(filepath)

    def load(self, filepath: str) -> None:
        """모델 로드"""
        self.model = keras.models.load_model(filepath)
