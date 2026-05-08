import pandas as pd
import numpy as np


def compute_technical_indicators(hist: pd.DataFrame) -> dict:
    """Compute technical analysis indicators from historical price data."""
    if hist.empty or len(hist) < 20:
        return {}

    close = hist["Close"]
    high = hist["High"]
    low = hist["Low"]
    volume = hist["Volume"]

    indicators = {}

    # Moving Averages
    indicators["ma20"] = round(close.rolling(20).mean().iloc[-1], 2) if len(close) >= 20 else None
    indicators["ma50"] = round(close.rolling(50).mean().iloc[-1], 2) if len(close) >= 50 else None
    indicators["ma200"] = round(close.rolling(200).mean().iloc[-1], 2) if len(close) >= 200 else None

    current_price = close.iloc[-1]
    indicators["above_ma20"] = current_price > indicators["ma20"] if indicators["ma20"] else None
    indicators["above_ma50"] = current_price > indicators["ma50"] if indicators["ma50"] else None
    indicators["above_ma200"] = current_price > indicators["ma200"] if indicators["ma200"] else None

    # MA cross signal
    if indicators["ma50"] and indicators["ma200"]:
        indicators["golden_cross"] = indicators["ma50"] > indicators["ma200"]

    # RSI (14-period)
    indicators["rsi"] = _compute_rsi(close, 14)

    # MACD (12, 26, 9)
    macd_data = _compute_macd(close)
    indicators.update(macd_data)

    # Bollinger Bands (20-period, 2 std)
    bb_data = _compute_bollinger(close)
    indicators.update(bb_data)

    # Average True Range (volatility)
    indicators["atr_14"] = _compute_atr(high, low, close, 14)

    # Volume trend
    avg_vol_20 = volume.rolling(20).mean().iloc[-1]
    avg_vol_50 = volume.rolling(50).mean().iloc[-1] if len(volume) >= 50 else avg_vol_20
    indicators["volume_trend"] = "increasing" if avg_vol_20 > avg_vol_50 else "decreasing"

    # Support and Resistance (simple pivot levels)
    recent_high = high.rolling(20).max().iloc[-1]
    recent_low = low.rolling(20).min().iloc[-1]
    pivot = (recent_high + recent_low + current_price) / 3
    indicators["pivot"] = round(pivot, 2)
    indicators["resistance_1"] = round(2 * pivot - recent_low, 2)
    indicators["support_1"] = round(2 * pivot - recent_high, 2)

    # Trend strength
    indicators["trend"] = _determine_trend(close, indicators)

    return indicators


def _compute_rsi(close: pd.Series, period: int = 14) -> float | None:
    if len(close) < period + 1:
        return None
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(window=period).mean()
    loss = (-delta.clip(upper=0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    val = rsi.iloc[-1]
    return round(val, 1) if not np.isnan(val) else None


def _compute_macd(close: pd.Series) -> dict:
    if len(close) < 26:
        return {}
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    histogram = macd_line - signal_line

    macd_val = macd_line.iloc[-1]
    signal_val = signal_line.iloc[-1]
    hist_val = histogram.iloc[-1]
    hist_prev = histogram.iloc[-2] if len(histogram) > 1 else hist_val

    return {
        "macd": round(macd_val, 4),
        "macd_signal": round(signal_val, 4),
        "macd_histogram": round(hist_val, 4),
        "macd_bullish": macd_val > signal_val,
        "macd_momentum": "increasing" if hist_val > hist_prev else "decreasing",
    }


def _compute_bollinger(close: pd.Series, period: int = 20) -> dict:
    if len(close) < period:
        return {}
    ma = close.rolling(period).mean()
    std = close.rolling(period).std()
    upper = ma + 2 * std
    lower = ma - 2 * std

    current = close.iloc[-1]
    upper_val = upper.iloc[-1]
    lower_val = lower.iloc[-1]
    ma_val = ma.iloc[-1]
    bandwidth = (upper_val - lower_val) / ma_val * 100 if ma_val != 0 else 0

    # %B indicator: position within bands
    pct_b = (current - lower_val) / (upper_val - lower_val) if (upper_val - lower_val) != 0 else 0.5

    return {
        "bb_upper": round(upper_val, 2),
        "bb_middle": round(ma_val, 2),
        "bb_lower": round(lower_val, 2),
        "bb_bandwidth": round(bandwidth, 2),
        "bb_pct_b": round(pct_b, 3),
        "bb_squeeze": bandwidth < 10,
    }


def _compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float | None:
    if len(close) < period + 1:
        return None
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs(),
    ], axis=1).max(axis=1)
    atr = tr.rolling(period).mean().iloc[-1]
    return round(atr, 2) if not np.isnan(atr) else None


def _determine_trend(close: pd.Series, indicators: dict) -> str:
    """Determine overall trend based on price and moving averages."""
    bullish_signals = 0
    bearish_signals = 0

    if indicators.get("above_ma20"):
        bullish_signals += 1
    else:
        bearish_signals += 1

    if indicators.get("above_ma50"):
        bullish_signals += 1
    else:
        bearish_signals += 1

    if indicators.get("above_ma200"):
        bullish_signals += 1
    else:
        bearish_signals += 1

    if indicators.get("golden_cross"):
        bullish_signals += 1
    elif indicators.get("golden_cross") is not None:
        bearish_signals += 1

    if bullish_signals >= 3:
        return "strong uptrend"
    elif bullish_signals == 2:
        return "uptrend"
    elif bearish_signals >= 3:
        return "strong downtrend"
    elif bearish_signals == 2:
        return "downtrend"
    else:
        return "sideways"
