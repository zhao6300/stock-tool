import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from quant_platform.cli import build_parser, run_backtest


class CliTests(unittest.TestCase):
    def test_build_parser_defaults(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["backtest", "600519"])

        self.assertEqual(args.code, "600519")
        self.assertEqual(args.days, 365)
        self.assertEqual(args.fast, 20)
        self.assertEqual(args.slow, 60)
        self.assertEqual(args.capital, 100000.0)
        self.assertEqual(args.cost, 0.0)
        self.assertEqual(args.format, "text")

    @patch("quant_platform.cli.run_stock_backtest")
    @patch("quant_platform.cli.create_session")
    def test_run_backtest_passes_shared_session(
        self,
        create_session_mock,
        run_stock_backtest_mock,
    ) -> None:
        session = object()
        create_session_mock.return_value = session
        result = {
            "stock": {"symbol": "sh600519"},
            "backtest": {
                "initial_capital": 100000.0,
                "final_equity": 101000.0,
                "total_return": 0.01,
                "annualized_return": 0.02,
                "annualized_volatility": 0.1,
                "sharpe_ratio": 0.2,
                "sortino_ratio": 0.3,
                "max_drawdown": -0.01,
                "transaction_costs": 0.0,
                "trade_count": 1,
            },
        }
        run_stock_backtest_mock.return_value = result
        parser = build_parser()
        args = parser.parse_args(["backtest", "600519"])

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            run_backtest(args)

        self.assertIs(run_stock_backtest_mock.call_args.kwargs["session"], session)
        self.assertIn("final_equity=101000.00", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
