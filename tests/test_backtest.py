import unittest

from quant_platform.backtest import (
    backtest_ma_cross,
    backtest_position_strategy,
    moving_average_crossover_positions,
    moving_average_crossover_signals,
)


class BacktestTests(unittest.TestCase):
    def test_backtest_ma_cross_with_buy_and_hold(self) -> None:
        bars = [{"close": float(price)} for price in range(1, 51)]
        result = backtest_ma_cross(bars, fast=2, slow=5, initial_capital=1000)
        self.assertGreater(result["final_equity"], result["initial_capital"])
        self.assertGreater(result["trade_count"], 0)

    def test_backtest_ma_cross_constant_values(self) -> None:
        bars = [{"close": 1.0} for _ in range(30)]
        result = backtest_ma_cross(bars, fast=2, slow=5)
        self.assertAlmostEqual(result["total_return"], 0.0)
        self.assertEqual(result["trade_count"], 0)

    def test_backtest_includes_buy_and_hold_benchmark(self) -> None:
        bars = [{"close": price} for price in (10.0, 11.0, 12.0)]
        result = backtest_ma_cross(
            bars,
            fast=2,
            slow=3,
            initial_capital=1000.0,
        )

        self.assertAlmostEqual(result["benchmark"]["total_return"], 0.2)
        self.assertIn("annualized_volatility", result["benchmark"])
        self.assertIn("sharpe_ratio", result["benchmark"])
        self.assertIn("sortino_ratio", result["benchmark"])
        self.assertIn("max_drawdown", result["benchmark"])

    def test_backtest_position_strategy(self) -> None:
        bars = [{"close": price} for price in (10.0, 11.0, 12.0)]
        positions = [0, 1, 0]

        result = backtest_position_strategy(
            bars,
            positions=positions,
            initial_capital=1000.0,
            transaction_cost_rate=0.0,
        )

        self.assertEqual(result["trade_count"], 2)
        self.assertGreater(result["total_return"], 0.0)
        self.assertAlmostEqual(result["final_equity"], 1000 * 12 / 11)

    def test_moving_average_crossover_positions(self) -> None:
        closes = [float(value) for value in range(1, 11)]
        positions = moving_average_crossover_positions(closes, fast=2, slow=5)
        self.assertEqual(len(positions), len(closes))
        self.assertTrue(set(positions).issubset({0, 1}))

    def test_backtest_cost_rate(self) -> None:
        bars = [{"close": float(price)} for price in range(1, 51)]
        without_cost = backtest_ma_cross(bars, fast=2, slow=5)
        with_cost = backtest_ma_cross(
            bars,
            fast=2,
            slow=5,
            transaction_cost_rate=0.001,
        )
        self.assertGreaterEqual(without_cost["total_return"], with_cost["total_return"])

    def test_backtest_requires_data(self) -> None:
        with self.assertRaises(ValueError):
            backtest_ma_cross([])
