import unittest

from quant_platform.indicators import (
    bollinger_bands,
    macd,
    momentum,
    relative_strength,
    simple_moving_average,
)


class IndicatorTests(unittest.TestCase):
    def test_simple_moving_average(self) -> None:
        result = simple_moving_average([1.0, 2.0, 3.0], 2)
        self.assertEqual(len(result), 3)
        self.assertIsNone(result[0])
        self.assertAlmostEqual(result[1], 1.5)
        self.assertAlmostEqual(result[2], 2.5)

    def test_simple_moving_average_short_series(self) -> None:
        self.assertEqual(
            simple_moving_average([1.0], 2),
            [None],
        )

    def test_momentum_requires_history(self) -> None:
        self.assertIsNone(momentum([1.0], 2))
        self.assertAlmostEqual(momentum([1.0, 1.1], 1), 0.1)

    def test_rsi_is_bounded(self) -> None:
        result = relative_strength(
            [
                1.0,
                1.1,
                1.2,
                1.15,
                1.25,
                1.3,
                1.4,
                1.5,
                1.45,
            ]
        )
        if result is not None:
            self.assertGreaterEqual(result, 0.0)
            self.assertLessEqual(result, 100.0)

    def test_macd_empty_values(self) -> None:
        self.assertIsNone(macd([1.0, 2.0], 3, 6, 3))

    def test_macd_constant_values(self) -> None:
        values = [1.0] * 30
        self.assertAlmostEqual(macd(values, 12, 26, 9), 0.0)
        self.assertIsNotNone(bollinger_bands(values, 10))
