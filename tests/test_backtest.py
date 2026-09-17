import unittest

from quant_platform.backtest import (
    backtest_ma_cross,
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
