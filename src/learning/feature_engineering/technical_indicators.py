"""
Technical Indicators for Feature Engineering

Utility functions for calculating technical indicators like RSI, MACD, etc.
"""
import pandas as pd
import numpy as np
from typing import Tuple


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate RSI (Relative Strength Index)

    Args:
        series: Price series (usually close price)
        period: RSI period (default: 14)

    Returns:
        RSI values (0-100)
    """
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate MACD (Moving Average Convergence Divergence)

    Args:
        series: Price series (usually close price)
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line period

    Returns:
        (MACD line, Signal line, Histogram)
    """
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()

    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def calculate_bollinger_bands(
    series: pd.Series,
    period: int = 20,
    std_dev: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Bollinger Bands

    Args:
        series: Price series
        period: Moving average period
        std_dev: Standard deviation multiplier

    Returns:
        (Upper band, Middle band, Lower band)
    """
    middle_band = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()

    upper_band = middle_band + (std * std_dev)
    lower_band = middle_band - (std * std_dev)

    return upper_band, middle_band, lower_band


def calculate_moving_average(series: pd.Series, period: int) -> pd.Series:
    """Calculate Simple Moving Average (SMA)"""
    return series.rolling(window=period).mean()


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average (EMA)"""
    return series.ewm(span=period, adjust=False).mean()


def calculate_ma_deviation(
    close: pd.Series,
    ma: pd.Series
) -> pd.Series:
    """
    Calculate moving average deviation (이격도)

    Args:
        close: Close price series
        ma: Moving average series

    Returns:
        Deviation ratio (close / ma * 100)
    """
    return (close / ma) * 100


def is_ma_aligned(
    ma_short: pd.Series,
    ma_mid: pd.Series,
    ma_long: pd.Series
) -> pd.Series:
    """
    Check if moving averages are in alignment (정배열)

    Args:
        ma_short: Short-term MA
        ma_mid: Mid-term MA
        ma_long: Long-term MA

    Returns:
        Boolean series (True if aligned: short > mid > long)
    """
    return (ma_short > ma_mid) & (ma_mid > ma_long)


def detect_volume_spike(
    volume: pd.Series,
    lookback: int = 20,
    threshold: float = 2.0
) -> pd.Series:
    """
    Detect volume spikes

    Args:
        volume: Volume series
        lookback: Lookback period for average
        threshold: Spike threshold (e.g., 2.0 = 2x average)

    Returns:
        Boolean series (True if volume spike)
    """
    avg_volume = volume.rolling(window=lookback).mean()
    ratio = volume / avg_volume

    return ratio >= threshold


def is_new_high(
    high: pd.Series,
    period_months: int
) -> pd.Series:
    """
    Check if current high is N-month high

    Args:
        high: High price series
        period_months: Period in months (1 month = ~20 trading days)

    Returns:
        Boolean series (True if new high)
    """
    period_days = period_months * 20  # Approximate trading days per month
    rolling_max = high.rolling(window=period_days).max()

    return high >= rolling_max


def is_new_volume_high(
    volume: pd.Series,
    period_months: int
) -> pd.Series:
    """
    Check if current volume is N-month high

    Args:
        volume: Volume series
        period_months: Period in months

    Returns:
        Boolean series (True if new volume high)
    """
    period_days = period_months * 20
    rolling_max = volume.rolling(window=period_days).max()

    return volume >= rolling_max


def calculate_price_change(
    close: pd.Series,
    periods: int
) -> pd.Series:
    """
    Calculate price change percentage

    Args:
        close: Close price series
        periods: Number of periods to look back

    Returns:
        Percentage change
    """
    return close.pct_change(periods) * 100


def calculate_high_low_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """
    Calculate high-low range normalized by close price

    Args:
        high: High price series
        low: Low price series
        close: Close price series

    Returns:
        (high - low) / close ratio
    """
    return (high - low) / close


def normalize_minmax(series: pd.Series, feature_range: Tuple[float, float] = (0, 1)) -> pd.Series:
    """
    Min-Max normalization

    Args:
        series: Input series
        feature_range: Target range (min, max)

    Returns:
        Normalized series
    """
    min_val = series.min()
    max_val = series.max()

    if max_val == min_val:
        return pd.Series(feature_range[0], index=series.index)

    normalized = (series - min_val) / (max_val - min_val)
    normalized = normalized * (feature_range[1] - feature_range[0]) + feature_range[0]

    return normalized


def normalize_zscore(series: pd.Series) -> pd.Series:
    """
    Z-score normalization (standardization)

    Args:
        series: Input series

    Returns:
        Normalized series (mean=0, std=1)
    """
    mean = series.mean()
    std = series.std()

    if std == 0:
        return pd.Series(0, index=series.index)

    return (series - mean) / std


def log_transform(series: pd.Series) -> pd.Series:
    """
    Log transformation (handles zeros)

    Args:
        series: Input series

    Returns:
        log(series + 1)
    """
    return np.log1p(series)
