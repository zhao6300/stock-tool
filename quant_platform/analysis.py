"""Pure analysis helpers. No network access."""

from __future__ import annotations

from typing import Sequence

from .metrics import annualized_return, annualized_volatility, maximum_drawdown, returns, trailing_mean
from .metrics import sharpe_ratio, sortino_ratio
from .risk import expected_shortfall, value_at_risk
from .indicators import bollinger_bands, macd, momentum, relative_strength


def analyze_stock_history(history: list[dict[str, float | str]], symbol: str) -> dict[str, object]:
    if not history:
        raise ValueError(f"No history available for {symbol}.")

    closes = [float(row["close"]) for row in history]
    volumes = [float(row["volume"]) for row in history]
    daily_returns = returns(closes)
    start_close = closes[0]
    latest_close = closes[-1]
    ma5 = trailing_mean(closes, 5)
    ma20 = trailing_mean(closes, 20)
    ma60 = trailing_mean(closes, 60)

    if ma20 is None or ma60 is None:
        trend = "样本不足，暂无法判断短中期趋势"
    elif latest_close > ma20 and ma20 > ma60:
        trend = "短中期趋势向上"
    elif latest_close < ma20 and ma20 < ma60:
        trend = "短中期趋势向下"
    else:
        trend = "短期震荡"

    return {
        "symbol": symbol,
        "start_date": history[0]["date"],
        "end_date": history[-1]["date"],
        "bars": len(history),
        "start_close": start_close,
        "latest_close": latest_close,
        "period_return": latest_close / start_close - 1 if start_close > 0 else 0.0,
        "annualized_return": annualized_return(closes),
        "annualized_volatility": annualized_volatility(daily_returns),
        "max_drawdown": maximum_drawdown(closes),
        "sharpe_ratio": sharpe_ratio(daily_returns),
        "sortino_ratio": sortino_ratio(daily_returns),
        "value_at_risk_95": value_at_risk(daily_returns, 0.95),
        "expected_shortfall_95": expected_shortfall(daily_returns, 0.95),
        "ma5": ma5,
        "ma20": ma20,
        "ma60": ma60,
        "volume_ma5": trailing_mean(volumes, 5),
        "volume_ma20": trailing_mean(volumes, 20),
        "momentum_5d": momentum(closes, 5),
        "momentum_20d": momentum(closes, 20),
        "rsi_14": relative_strength(closes, 14),
        "macd": macd(closes),
        "bollinger_20_2": bollinger_bands(closes, 20, 2.0),
        "trend": trend,
    }
