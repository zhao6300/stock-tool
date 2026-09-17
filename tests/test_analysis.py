import unittest

from quant_platform.metrics import (
    annualized_return,
    annualized_volatility,
    maximum_drawdown,
    returns,
    sharpe_ratio,
    sortino_ratio,
    standard_deviation,
    trailing_mean,
)
from quant_platform.indicators import bollinger_bands, macd, relative_strength
from quant_platform.analysis import analyze_stock_history


class AnalysisTests(unittest.TestCase):
    def test_percent_returns(self) -> None:
        result = returns([10.0, 11.0])
        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result[0], 0.1)

    def test_standard_deviation(self) -> None:
        self.assertAlmostEqual(standard_deviation([1.0, 2.0, 3.0]), 1.0)

    def test_stock_history_analysis(self) -> None:
        history = [
            {"date": "2026-01-01", "close": 10.0, "volume": 100.0},
            {"date": "2026-01-02", "close": 11.0, "volume": 120.0},
            {"date": "2026-01-03", "close": 12.0, "volume": 140.0},
        ]
        analysis = analyze_stock_history(history, "sh000001")
        self.assertEqual(analysis["bars"], 3)
        self.assertAlmostEqual(analysis["latest_close"], 12.0)
        self.assertAlmostEqual(analysis["period_return"], 0.2)
        self.assertEqual(analysis["trend"], "样本不足，暂无法判断短中期趋势")

    def test_maximum_drawdown(self) -> None:
        self.assertAlmostEqual(maximum_drawdown([10.0, 12.0, 6.0, 8.0]), -0.5)

    def test_trailing_mean_window(self) -> None:
        self.assertIsNone(trailing_mean([1.0], 2))
        self.assertAlmostEqual(trailing_mean([1.0, 3.0], 2), 2.0)

    def test_annualized_return(self) -> None:
        closes = [1.0 * (1.1 ** (day / 252.0)) for day in range(252)]
        self.assertAlmostEqual(annualized_return(closes), 0.1)

    def test_sharpe_and_sortino_no_risk(self) -> None:
        self.assertEqual(sharpe_ratio([0.0]), 0.0)
        self.assertEqual(sortino_ratio([0.0]), 0.0)
