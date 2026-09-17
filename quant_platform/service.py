"""Business orchestration layer between data adapters, analysis and CLI."""

from __future__ import annotations

import requests

from .analysis import analyze_stock_history
from .backtest import backtest_ma_cross
from .data_sources import (
    DEFAULT_SECTORS,
    create_session,
    fetch_sector_snapshot,
    fetch_stock_history,
)


def get_stock_analysis(
    code: str,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    days: int = 365,
) -> dict[str, object]:
    session = create_session()
    stock_data = fetch_stock_history(
        session,
        code,
        end_date=end_date,
        days=days,
        start_date=start_date,
    )
    return {
        "stock": stock_data,
        "analysis": analyze_stock_history(stock_data["history"], stock_data["symbol"]),
    }


def get_sector_snapshot(name: str) -> dict[str, object]:
    session = create_session()
    return fetch_sector_snapshot(session, name)


def run_stock_backtest(
    code: str,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    days: int = 365,
    fast: int = 20,
    slow: int = 60,
    initial_capital: float = 100_000.0,
    transaction_cost_rate: float = 0.0,
) -> dict[str, object]:
    session = create_session()
    stock_data = fetch_stock_history(
        session,
        code,
        end_date=end_date,
        days=days,
        start_date=start_date,
    )
    return {
        "stock": stock_data,
        "backtest": backtest_ma_cross(
            stock_data["history"],
            fast=fast,
            slow=slow,
            initial_capital=initial_capital,
            transaction_cost_rate=transaction_cost_rate,
        ),
    }
