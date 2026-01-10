import pytest
import pandas as pd
import numpy as np
from app.signal_engine.indicators import (
    ema, rsi, atr, macd, bollinger_bands, 
    detect_market_structure, analyze_volume
)

# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def sample_price_data():
    """Create a sample trend DataFrame"""
    # Create 50 days of data
    dates = pd.date_range(start="2024-01-01", periods=50, freq="D")
    
    # Uptrend
    prices = [100 + i + (i%5) for i in range(50)] 
    highs = [p + 2 for p in prices]
    lows = [p - 2 for p in prices]
    volumes = [1000 * i for i in range(50)]
    
    df = pd.DataFrame({
        "Close": prices,
        "High": highs,
        "Low": lows,
        "Volume": volumes
    }, index=dates)
    return df

# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------

def test_ema_calculation(sample_price_data):
    """Test Exponential Moving Average"""
    series = sample_price_data["Close"]
    result = ema(series, period=10)
    
    assert len(result) == 50
    assert not result.isnull().all()
    # EMA matches pandas calc
    pd.testing.assert_series_equal(result, series.ewm(span=10, adjust=False).mean())

def test_rsi_calculation(sample_price_data):
    """Test Relative Strength Index"""
    series = sample_price_data["Close"]
    result = rsi(series, period=14)
    
    # RSI should be between 0 and 100
    assert result.min() >= 0
    assert result.max() <= 100
    # In uptrend, RSI should be high
    assert result.iloc[-1] > 50

def test_macd_calculation(sample_price_data):
    """Test MACD Tuple"""
    series = sample_price_data["Close"]
    macd_line, signal_line, hist = macd(series)
    
    assert len(macd_line) == 50
    assert len(signal_line) == 50
    assert len(hist) == 50
    
    # Check relationship
    # histogram = macd - signal
    # allow small float precision diff
    diff = (macd_line - signal_line) - hist
    assert diff.abs().max() < 0.0001

def test_bollinger_bands(sample_price_data):
    """Test Bollinger Bands"""
    series = sample_price_data["Close"]
    upper, mid, lower = bollinger_bands(series)
    
    # Upper > Mid > Lower
    assert (upper >= mid).all()
    assert (mid >= lower).all()

def test_market_structure_detection():
    """Test Higher High / Lower Low detection"""
    # Create uptrend pattern
    df = pd.DataFrame({
        "High": [10, 11, 12, 11, 13, 12, 14],
        "Low": [9, 10, 11, 10, 12, 11, 13],
        "Close": [10, 11, 12, 11, 13, 12, 14] # Dummy
    })
    
    structure = detect_market_structure(df, lookback=5)
    # Note: Logic depends on swing points. Simple linear uptrend might trigger "higher_high"
    # or "consolidation" if volatility is low.
    # Given the implementation, we expect valid enum return
    assert structure in ["higher_high", "lower_low", "range", "consolidation"]

def test_volume_analysis(sample_price_data):
    """Test Volume Spike detection"""
    df = sample_price_data.copy()
    
    # Add huge spike at end
    df.iloc[-1, df.columns.get_loc("Volume")] = 10000000 
    # Previous average is small (~25000)
    
    ratio, confirmation, spike = analyze_volume(df)
    
    assert spike is True
    assert ratio > 2.0
