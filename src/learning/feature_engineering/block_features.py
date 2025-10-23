"""
Block Pattern Features

Feature extraction functions for block pattern detection.
All features are registered with the global feature_registry.
"""
import pandas as pd
import numpy as np
from .registry import feature_registry
from .technical_indicators import (
    calculate_rsi, calculate_macd, calculate_bollinger_bands,
    calculate_moving_average, calculate_ema, calculate_ma_deviation,
    is_ma_aligned, detect_volume_spike, is_new_high, is_new_volume_high,
    calculate_price_change, calculate_high_low_range,
    normalize_minmax, normalize_zscore, log_transform
)


# ============================================================================
# PRICE FEATURES
# ============================================================================

@feature_registry.register(
    'price_close_normalized',
    category='price',
    description='Min-Max normalized close price'
)
def price_close_normalized(df: pd.DataFrame) -> pd.Series:
    """Normalized close price (0-1)"""
    return normalize_minmax(df['close'])


@feature_registry.register(
    'price_change_1d',
    category='price',
    description='1-day price change percentage'
)
def price_change_1d(df: pd.DataFrame) -> pd.Series:
    """1-day price change percentage"""
    return calculate_price_change(df['close'], 1)


@feature_registry.register(
    'price_change_5d',
    category='price',
    description='5-day price change percentage'
)
def price_change_5d(df: pd.DataFrame) -> pd.Series:
    """5-day price change percentage"""
    return calculate_price_change(df['close'], 5)


@feature_registry.register(
    'price_change_20d',
    category='price',
    description='20-day price change percentage'
)
def price_change_20d(df: pd.DataFrame) -> pd.Series:
    """20-day price change percentage"""
    return calculate_price_change(df['close'], 20)


@feature_registry.register(
    'price_high_vs_prev_close',
    category='price',
    description='High vs previous close ratio'
)
def price_high_vs_prev_close(df: pd.DataFrame) -> pd.Series:
    """High price vs previous close"""
    prev_close = df['close'].shift(1)
    return ((df['high'] - prev_close) / prev_close * 100).fillna(0)


@feature_registry.register(
    'price_high_low_range',
    category='price',
    description='High-low range / close'
)
def price_high_low_range(df: pd.DataFrame) -> pd.Series:
    """High-low range normalized by close"""
    return calculate_high_low_range(df['high'], df['low'], df['close'])


@feature_registry.register(
    'price_new_high_6m',
    category='price',
    description='Is 6-month new high (binary)'
)
def price_new_high_6m(df: pd.DataFrame) -> pd.Series:
    """Is 6-month new high"""
    return is_new_high(df['high'], 6).astype(int)


@feature_registry.register(
    'price_new_high_12m',
    category='price',
    description='Is 12-month new high (binary)'
)
def price_new_high_12m(df: pd.DataFrame) -> pd.Series:
    """Is 12-month new high"""
    return is_new_high(df['high'], 12).astype(int)


@feature_registry.register(
    'price_new_high_24m',
    category='price',
    description='Is 24-month new high (binary)'
)
def price_new_high_24m(df: pd.DataFrame) -> pd.Series:
    """Is 24-month new high"""
    return is_new_high(df['high'], 24).astype(int)


# ============================================================================
# VOLUME FEATURES
# ============================================================================

@feature_registry.register(
    'volume_normalized',
    category='volume',
    description='Min-Max normalized volume'
)
def volume_normalized(df: pd.DataFrame) -> pd.Series:
    """Normalized volume (0-1)"""
    return normalize_minmax(df['volume'])


@feature_registry.register(
    'volume_log_normalized',
    category='volume',
    description='Log-transformed and normalized volume'
)
def volume_log_normalized(df: pd.DataFrame) -> pd.Series:
    """Log-transformed and normalized volume"""
    log_vol = log_transform(df['volume'])
    return normalize_minmax(log_vol)


@feature_registry.register(
    'volume_ma5_ratio',
    category='volume',
    description='Volume / MA5 ratio'
)
def volume_ma5_ratio(df: pd.DataFrame) -> pd.Series:
    """Volume divided by 5-day moving average"""
    ma5 = calculate_moving_average(df['volume'], 5)
    return (df['volume'] / ma5).fillna(1.0)


@feature_registry.register(
    'volume_ma20_ratio',
    category='volume',
    description='Volume / MA20 ratio'
)
def volume_ma20_ratio(df: pd.DataFrame) -> pd.Series:
    """Volume divided by 20-day moving average"""
    ma20 = calculate_moving_average(df['volume'], 20)
    return (df['volume'] / ma20).fillna(1.0)


@feature_registry.register(
    'volume_ma60_ratio',
    category='volume',
    description='Volume / MA60 ratio'
)
def volume_ma60_ratio(df: pd.DataFrame) -> pd.Series:
    """Volume divided by 60-day moving average"""
    ma60 = calculate_moving_average(df['volume'], 60)
    return (df['volume'] / ma60).fillna(1.0)


@feature_registry.register(
    'volume_spike_ratio',
    category='volume',
    description='Volume spike ratio (vs MA20)'
)
def volume_spike_ratio(df: pd.DataFrame) -> pd.Series:
    """Volume spike ratio compared to 20-day average"""
    ma20 = calculate_moving_average(df['volume'], 20)
    ratio = (df['volume'] / ma20).fillna(1.0)
    return ratio


@feature_registry.register(
    'volume_spike_2x',
    category='volume',
    description='Volume spike >= 2x average (binary)'
)
def volume_spike_2x(df: pd.DataFrame) -> pd.Series:
    """Volume spike >= 2x average"""
    return detect_volume_spike(df['volume'], 20, 2.0).astype(int)


@feature_registry.register(
    'volume_spike_3x',
    category='volume',
    description='Volume spike >= 3x average (binary)'
)
def volume_spike_3x(df: pd.DataFrame) -> pd.Series:
    """Volume spike >= 3x average"""
    return detect_volume_spike(df['volume'], 20, 3.0).astype(int)


@feature_registry.register(
    'volume_new_high_6m',
    category='volume',
    description='Is 6-month new volume high (binary)'
)
def volume_new_high_6m(df: pd.DataFrame) -> pd.Series:
    """Is 6-month new volume high"""
    return is_new_volume_high(df['volume'], 6).astype(int)


@feature_registry.register(
    'volume_new_high_12m',
    category='volume',
    description='Is 12-month new volume high (binary)'
)
def volume_new_high_12m(df: pd.DataFrame) -> pd.Series:
    """Is 12-month new volume high"""
    return is_new_volume_high(df['volume'], 12).astype(int)


@feature_registry.register(
    'volume_new_high_24m',
    category='volume',
    description='Is 24-month new volume high (binary)'
)
def volume_new_high_24m(df: pd.DataFrame) -> pd.Series:
    """Is 24-month new volume high"""
    return is_new_volume_high(df['volume'], 24).astype(int)


@feature_registry.register(
    'volume_prev_day_ratio',
    category='volume',
    description='Volume vs previous day ratio'
)
def volume_prev_day_ratio(df: pd.DataFrame) -> pd.Series:
    """Volume divided by previous day volume"""
    prev_volume = df['volume'].shift(1)
    return (df['volume'] / prev_volume).fillna(1.0)


# ============================================================================
# TRADING VALUE FEATURES
# ============================================================================

@feature_registry.register(
    'trading_value_billion',
    category='trading_value',
    description='Trading value in billion won'
)
def trading_value_billion(df: pd.DataFrame) -> pd.Series:
    """Trading value in billion won"""
    trading_value = df['close'] * df['volume']
    return trading_value / 100_000_000  # Convert to billion


@feature_registry.register(
    'trading_value_normalized',
    category='trading_value',
    description='Normalized trading value'
)
def trading_value_normalized(df: pd.DataFrame) -> pd.Series:
    """Normalized trading value"""
    trading_value = df['close'] * df['volume']
    return normalize_minmax(trading_value)


@feature_registry.register(
    'trading_value_ma20_ratio',
    category='trading_value',
    description='Trading value / MA20 ratio'
)
def trading_value_ma20_ratio(df: pd.DataFrame) -> pd.Series:
    """Trading value divided by 20-day MA"""
    trading_value = df['close'] * df['volume']
    ma20 = calculate_moving_average(trading_value, 20)
    return (trading_value / ma20).fillna(1.0)


@feature_registry.register(
    'trading_value_above_300b',
    category='trading_value',
    description='Trading value >= 300 billion (binary)'
)
def trading_value_above_300b(df: pd.DataFrame) -> pd.Series:
    """Trading value >= 300 billion won"""
    trading_value_b = trading_value_billion(df)
    return (trading_value_b >= 300).astype(int)


@feature_registry.register(
    'trading_value_above_1500b',
    category='trading_value',
    description='Trading value >= 1500 billion (binary)'
)
def trading_value_above_1500b(df: pd.DataFrame) -> pd.Series:
    """Trading value >= 1500 billion won"""
    trading_value_b = trading_value_billion(df)
    return (trading_value_b >= 1500).astype(int)


# ============================================================================
# MOVING AVERAGE FEATURES
# ============================================================================

@feature_registry.register(
    'ma5',
    category='ma',
    description='5-day moving average'
)
def ma5(df: pd.DataFrame) -> pd.Series:
    """5-day moving average"""
    return calculate_moving_average(df['close'], 5)


@feature_registry.register(
    'ma20',
    category='ma',
    description='20-day moving average'
)
def ma20(df: pd.DataFrame) -> pd.Series:
    """20-day moving average"""
    return calculate_moving_average(df['close'], 20)


@feature_registry.register(
    'ma60',
    category='ma',
    description='60-day moving average'
)
def ma60(df: pd.DataFrame) -> pd.Series:
    """60-day moving average"""
    return calculate_moving_average(df['close'], 60)


@feature_registry.register(
    'ma120',
    category='ma',
    description='120-day moving average'
)
def ma120(df: pd.DataFrame) -> pd.Series:
    """120-day moving average"""
    return calculate_moving_average(df['close'], 120)


@feature_registry.register(
    'ma_deviation_60',
    category='ma',
    description='MA60 deviation (close/MA * 100)'
)
def ma_deviation_60(df: pd.DataFrame) -> pd.Series:
    """MA60 deviation (이격도)"""
    ma = calculate_moving_average(df['close'], 60)
    return calculate_ma_deviation(df['close'], ma)


@feature_registry.register(
    'ma_deviation_120',
    category='ma',
    description='MA120 deviation (close/MA * 100)'
)
def ma_deviation_120(df: pd.DataFrame) -> pd.Series:
    """MA120 deviation (이격도)"""
    ma = calculate_moving_average(df['close'], 120)
    return calculate_ma_deviation(df['close'], ma)


@feature_registry.register(
    'high_above_ma60',
    category='ma',
    description='High >= MA60 (binary)'
)
def high_above_ma60(df: pd.DataFrame) -> pd.Series:
    """High price >= MA60"""
    ma = calculate_moving_average(df['close'], 60)
    return (df['high'] >= ma).astype(int)


@feature_registry.register(
    'high_above_ma120',
    category='ma',
    description='High >= MA120 (binary)'
)
def high_above_ma120(df: pd.DataFrame) -> pd.Series:
    """High price >= MA120"""
    ma = calculate_moving_average(df['close'], 120)
    return (df['high'] >= ma).astype(int)


@feature_registry.register(
    'ma_alignment',
    category='ma',
    description='MA alignment (5 > 20 > 60) (binary)'
)
def ma_alignment(df: pd.DataFrame) -> pd.Series:
    """MA alignment (정배열): MA5 > MA20 > MA60"""
    ma5_val = calculate_moving_average(df['close'], 5)
    ma20_val = calculate_moving_average(df['close'], 20)
    ma60_val = calculate_moving_average(df['close'], 60)

    return is_ma_aligned(ma5_val, ma20_val, ma60_val).astype(int)


# ============================================================================
# TECHNICAL INDICATORS
# ============================================================================

@feature_registry.register(
    'rsi_14',
    category='technical',
    description='14-period RSI'
)
def rsi_14(df: pd.DataFrame) -> pd.Series:
    """RSI with 14-period"""
    return calculate_rsi(df['close'], 14)


@feature_registry.register(
    'macd',
    category='technical',
    description='MACD line'
)
def macd(df: pd.DataFrame) -> pd.Series:
    """MACD line"""
    macd_line, _, _ = calculate_macd(df['close'])
    return macd_line


@feature_registry.register(
    'macd_signal',
    category='technical',
    description='MACD signal line'
)
def macd_signal(df: pd.DataFrame) -> pd.Series:
    """MACD signal line"""
    _, signal_line, _ = calculate_macd(df['close'])
    return signal_line


@feature_registry.register(
    'macd_histogram',
    category='technical',
    description='MACD histogram'
)
def macd_histogram(df: pd.DataFrame) -> pd.Series:
    """MACD histogram"""
    _, _, histogram = calculate_macd(df['close'])
    return histogram


@feature_registry.register(
    'bollinger_width',
    category='technical',
    description='Bollinger band width'
)
def bollinger_width(df: pd.DataFrame) -> pd.Series:
    """Bollinger band width"""
    upper, middle, lower = calculate_bollinger_bands(df['close'])
    return (upper - lower) / middle


# ============================================================================
# BLOCK RELATIONSHIP FEATURES (Requires context)
# ============================================================================

@feature_registry.register(
    'block1_price_ratio',
    category='block_relation',
    description='Current price / Block1 high price',
    requires=['block1_high']
)
def block1_price_ratio(df: pd.DataFrame, block1_high: float) -> pd.Series:
    """Current close price / Block1 high price"""
    return df['close'] / block1_high


@feature_registry.register(
    'block1_volume_ratio',
    category='block_relation',
    description='Current volume / Block1 max volume',
    requires=['block1_max_volume']
)
def block1_volume_ratio(df: pd.DataFrame, block1_max_volume: float) -> pd.Series:
    """Current volume / Block1 max volume"""
    return df['volume'] / block1_max_volume


@feature_registry.register(
    'block1_days_since',
    category='block_relation',
    description='Days since Block1 ended',
    requires=['block1_end_date']
)
def block1_days_since(df: pd.DataFrame, block1_end_date: pd.Timestamp) -> pd.Series:
    """Days since Block1 ended"""
    days_diff = (df.index - block1_end_date).days
    return pd.Series(days_diff, index=df.index)


@feature_registry.register(
    'block1_support_distance',
    category='block_relation',
    description='Distance from Block1 support price',
    requires=['block1_spot_price']
)
def block1_support_distance(df: pd.DataFrame, block1_spot_price: float) -> pd.Series:
    """Distance from Block1 spot center price (percentage)"""
    return ((df['close'] - block1_spot_price) / block1_spot_price * 100)


# Initialize all features by importing this module
def initialize_features():
    """Initialize all features (called when module is imported)"""
    pass


# Auto-initialize
initialize_features()
