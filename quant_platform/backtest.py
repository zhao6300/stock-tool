"""Pure backtest helpers.  No network access."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from .indicators import simple_moving_average
from .metrics import annualized_volatility, returns, maximum_drawdown, sharpe_ratio, sortino_ratio


def _annualized_return(total_return: float, periods: int) -> float:
    if periods <= 0 or total_return <= -1.0:
        if periods <= 0:
            return 0.0
        return -1.0
    return (1.0 + total_return) ** (252.0 / periods) - 1.0


@dataclass(frozen=True)
class SignalRule:
    fast: int
    slow: int


def moving_average_crossover_signals(
    closes: Sequence[float],
    fast: int = 20,
    slow: int = 60,
) -> list[int]:
    """Return the desired position after each bar."""
    if fast <= 0:
        raise ValueError("fast must be positive")
    if slow <= fast:
        raise ValueError("slow must be greater than fast")
    fast_ma = simple_moving_average(closes, fast)
    slow_ma = simple_moving_average(closes, slow)
    signals = [0 for _ in closes]
    crossover = False
    for index in range(len(closes)):
        if fast_ma[index] is not None and slow_ma[index] is not None:
            crossover = bool(fast_ma[index] > slow_ma[index])  # type: ignore[arg-type]
        if crossover:
            signals[index] = 1
    return signals


def moving_average_crossover_positions(
    closes: Sequence[float],
    fast: int = 20,
    slow: int = 60,
) -> list[int]:
    signals = moving_average_crossover_signals(closes, fast, slow)
    positions = [0]
    for index in range(1, len(signals)):
        transition = signals[index] != signals[index - 1]
        if transition:
            positions.append(signals[index])
        else:
            positions.append(positions[index - 1])
    return positions


def apply_transaction_costs(
    equity_values: list[float],
    transaction_costs: Sequence[float],
) -> list[float]:
    result: list[float] = []
    for equity, cost in zip(equity_values, transaction_costs):
        result.append(equity - cost)
    return result


def backtest_ma_cross(
    bars: Sequence[dict[str, float | str]],
    *,
    fast: int = 20,
    slow: int = 60,
    initial_capital: float = 100_000.0,
    transaction_cost_rate: float = 0.0,
) -> dict[str, object]:
    if not bars:
        raise ValueError("No data.")
    if fast <= 0 or slow <= fast:
        raise ValueError("slow must be greater than fast")
    if initial_capital <= 0:
        raise ValueError("initial capital must be positive")
    if transaction_cost_rate < 0:
        raise ValueError("transaction cost rate must be non-negative")

    closes = [float(bar["close"]) for bar in bars]
    positions = moving_average_crossover_positions(closes, fast, slow)
    equity_values = [initial_capital]
    transaction_costs: list[float] = [0.0]
    current_shares = 0.0
    cash = initial_capital

    for index in range(1, len(closes)):
        previous_position = positions[index - 1]
        current_position = positions[index]
        cost = 0.0
        if current_position > previous_position:
            shares_to_buy = cash / closes[index]
            cost = shares_to_buy * closes[index] * transaction_cost_rate
            cash -= cost
            current_shares += shares_to_buy
        elif current_position < previous_position:
            proceeds = current_shares * closes[index]
            cost = proceeds * transaction_cost_rate
            cash += proceeds - cost
            current_shares = 0.0
        equity_values.append(cash + current_shares * closes[index])
        transaction_costs.append(cost)

    strategy_returns = returns(equity_values)
    total_return = equity_values[-1] / initial_capital - 1
    annualized_return_rate = _annualized_return(total_return, len(strategy_returns))
    benchmark_returns = returns(closes)
    benchmark_total_return = closes[-1] / closes[0] - 1 if closes[0] > 0 else 0.0
    trade_count = sum(
        1 for index in range(1, len(positions)) if positions[index] != positions[index - 1]
    )
    return {
        "initial_capital": initial_capital,
        "final_equity": equity_values[-1],
        "total_return": total_return,
        "annualized_return": annualized_return_rate,
        "annualized_volatility": annualized_volatility(strategy_returns),
        "sharpe_ratio": sharpe_ratio(strategy_returns),
        "sortino_ratio": sortino_ratio(strategy_returns),
        "max_drawdown": maximum_drawdown(equity_values),
        "transaction_costs": sum(transaction_costs),
        "trade_count": trade_count,
        "positions": positions,
        "equity_curve": equity_values,
        "benchmark": {
            "total_return": benchmark_total_return,
            "annualized_return": _annualized_return(
                benchmark_total_return,
                len(benchmark_returns),
            ),
            "annualized_volatility": annualized_volatility(benchmark_returns),
            "sharpe_ratio": sharpe_ratio(benchmark_returns),
            "sortino_ratio": sortino_ratio(benchmark_returns),
            "max_drawdown": maximum_drawdown(closes),
        },
    }
