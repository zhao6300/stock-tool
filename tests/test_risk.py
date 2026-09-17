import unittest

from quant_platform.risk import (
    calculate_beta,
    expected_shortfall,
    value_at_risk,
)


class RiskTests(unittest.TestCase):
    def test_value_at_risk(self) -> None:
        returns = [0.01, 0.02, -0.03, 0.04, -0.05]
        self.assertGreater(value_at_risk(returns, 0.8), 0.0)

    def test_expected_shortfall_non_negative(self) -> None:
        returns = [0.01, 0.02, -0.03, 0.04, -0.05]
        self.assertGreaterEqual(expected_shortfall(returns, 0.8), 0.0)

    def test_calculate_beta(self) -> None:
        self.assertAlmostEqual(calculate_beta([0.01, 0.02], [0.01, 0.02]), 1.0)

    def test_calculate_beta_requires_equal_length(self) -> None:
        with self.assertRaises(ValueError):
            calculate_beta([0.01], [0.01, 0.02])
