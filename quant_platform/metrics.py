"""Pure math helpers used by stocks and portfolios. No I/O."""

from __future__ import annotations

from math import sqrt
from typing import Iterable, Sequence


_ANNUALIZATION = 252.0


def to_floats(values: Iterable[float]) -> list[float]:
    return [float(value) for value in values]


def arithmetic_mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def sample_standard_deviation(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    center = arithmetic_mean(values)
    return sqrt(sum((value - center) ** 2 for value in values) / (len(values) - 1))


def returns(values: Sequence[float]) -> list[float]:
    if len(values) < 2:
        return []
    return [current / previous - 1 for previous, current in zip(values[:-1], values[1:])]


def annualized_return(closes: Sequence[float]) -> float:
    if len(closes) < 2 or closes[0] <= 0:
        return 0.0
    growth = closes[-1] / closes[0]
    periods = len(closes) - 1
    return growth ** (_ANNUALIZATION / periods) - 1


def annualized_volatility(values: Sequence[float]) -> float:
    return sample_standard_deviation(values) * sqrt(_ANNUALIZATION)


def downside_deviation(values: Sequence[float], target_return: float = 0.0) -> float:
    if len(values) < 2:
        return 0.0
    downside = [minimum(value - target_return, 0.0) ** 2 for value in values]
    return sqrt(sum(downside) / (len(values) - 1))


def minimum(values: float, other: float) -> float:
    return values if values < other else other


def sharpe_ratio(
    values: Sequence[float],
    risk_free_rate: float = 0.0,
) -> float:
    returns_values = values[-len(values) :] if values else []
    excess = [value - risk_free_rate for value in returns_values]
    deviation = sample_standard_deviation(excess)
    if deviation <= 0:
        return 0.0
    return arithmetic_mean(excess) / deviation * sqrt(_ANNUALIZATION)


def sortino_ratio(
    values: Sequence[float],
    risk_free_rate: float = 0.0,
) -> float:
    excess = [value - risk_free_rate for value in values]
    deviation = downside_deviation(excess)
    if deviation <= 0:
        return 0.0
    return arithmetic_mean(excess) / deviation * sqrt(_ANNUALIZATION)


def maximum_drawdown(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    peak = values[0]
    drawdown = 0.0
    for value in values:
        peak = max(peak, value)
        drawdown = min(drawdown, value / peak - 1 if peak > 0 else 0.0)
    return drawdown


def drawdown(values: Sequence[float]) -> float:
    """Standard drawdown expressed as a positive magnitude."""
    return -maximum_drawdown(values)


def trailing_mean(values: Sequence[float], window: int) -> float | None:
    if window <= 0 or len(values) < window:
        return None
    return arithmetic_mean(values[-window:])


def rolling_mean(values: Sequence[float], window: int) -> list[float] | None:
    if window <= 0 or len(values) < window:
        return None
    return [sum(values[index - window + 1 : index + 1]) / window for index in range(len(values))][window - 1 :]


def standard_deviation(values: Sequence[float]) -> float:
    return sample_standard_deviation(values)
