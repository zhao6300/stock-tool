"""Pure risk helpers. No network access."""

from __future__ import annotations

from typing import Sequence

from .metrics import (
    arithmetic_mean,
    annualized_return,
    annualized_volatility,
    maximum_drawdown,
    returns,
    sharpe_ratio,
    sortino_ratio,
)


def value_at_risk(daily_returns: Sequence[float], confidence: float = 0.95) -> float:
    """Return positive loss threshold such that losses exceed it with confidence level."""
    if not daily_returns:
        return 0.0
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")
    alpha = 1.0 - confidence
    ordered = sorted(float(value) for value in daily_returns)
    index = min(int(len(ordered) * alpha), len(ordered) - 1)
    return -ordered[index]


def expected_shortfall(daily_returns: Sequence[float], confidence: float = 0.95) -> float:
    """Return average loss beyond Value-at-Risk."""
    if not daily_returns:
        return 0.0
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")
    alpha = 1.0 - confidence
    threshold = value_at_risk(daily_returns, confidence)
    tail = [value for value in daily_returns if value <= -threshold]
    return -arithmetic_mean(tail) if tail else threshold


def alpha(
    portfolio_returns: Sequence[float],
    benchmark_returns: Sequence[float],
    risk_free_rate: float = 0.0,
) -> float:
    """Return excess return above CAPM expected return."""
    if len(portfolio_returns) != len(benchmark_returns):
        raise ValueError("portfolio and benchmark returns must have the same length")
    if not portfolio_returns:
        return 0.0
    beta = calculate_beta(portfolio_returns, benchmark_returns)
    expected = risk_free_rate + beta * (
        arithmetic_mean(benchmark_returns) - risk_free_rate
    )
    return arithmetic_mean(portfolio_returns) - expected


def calculate_beta(portfolio_returns: Sequence[float], benchmark_returns: Sequence[float]) -> float:
    if len(portfolio_returns) != len(benchmark_returns):
        raise ValueError("portfolio and benchmark returns must have the same length")
    if len(portfolio_returns) < 2:
        return 0.0
    portfolio_mean = arithmetic_mean(portfolio_returns)
    benchmark_mean = arithmetic_mean(benchmark_returns)
    covariance = sum(
        (portfolio - portfolio_mean) * (benchmark - benchmark_mean)
        for portfolio, benchmark in zip(portfolio_returns, benchmark_returns)
    )
    variance = sum((value - benchmark_mean) ** 2 for value in benchmark_returns)
    if variance == 0:
        return 0.0
    return covariance / variance
