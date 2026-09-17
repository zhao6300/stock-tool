"""Pure indicator calculations. No network I/O."""

from __future__ import annotations

from typing import Optional, Sequence

from .metrics import arithmetic_mean, standard_deviation, to_floats, trailing_mean


def exponential_moving_average(values: Sequence[float], window: int) -> Optional[float]:
    window = max(window, 2)
    values = to_floats(values)
    if len(values) < window:
        return None
    multiplier = 2.0 / (window + 1.0)
    result = arithmetic_mean(values[:window])
    for value in values[window:]:
        result = value * multiplier + result * (1.0 - multiplier)
    return result


def simple_moving_average(values: Sequence[float], window: int) -> list[Optional[float]]:
    if window <= 0 or len(values) < window:
        return [None] * len(values)
    output: list[Optional[float]] = [None] * len(values)
    rolling_mean = sum(values[:window]) / window
    output[window - 1] = rolling_mean
    for index in range(window, len(values)):
        rolling_mean += (values[index] - values[index - window]) / window
        output[index] = rolling_mean
    return output
def momentum(values: Sequence[float], window: int) -> Optional[float]:
    values = to_floats(values)
    if window <= 0 or len(values) <= window:
        return None
    return values[-1] / values[-window - 1] - 1


def relative_strength(values: Sequence[float], periods: int = 14) -> Optional[float]:
    values = to_floats(values)
    if periods <= 0 or len(values) <= periods:
        return None
    gains = losses = 0.0
    for previous, current in zip(values[-(periods + 1) : -1], values[-periods:]):
        change = current - previous
        if change > 0:
            gains += change
        else:
            losses -= change
    if gains + losses == 0:
        return 50.0
    rs = gains / (losses if losses > 0 else 1e-12)
    return 100.0 * rs / (1.0 + rs)


def bollinger_bands(values: Sequence[float], window: int = 20, multiplier: float = 2.0):
    values = to_floats(values)
    middle = trailing_mean(values, window)
    if middle is None:
        return None
    std = standard_deviation(values[-window:])
    return {"middle": middle, "upper": middle + std * multiplier, "lower": middle - std * multiplier}


def macd(
    values: Sequence[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> Optional[float]:
    values = to_floats(values)
    if len(values) <= max(slow, signal):
        return None
    macd_line = exponential_moving_average(values, fast)
    signal_line = exponential_moving_average(values, slow)
    if macd_line is None or signal_line is None:
        return None
    return macd_line - signal_line
