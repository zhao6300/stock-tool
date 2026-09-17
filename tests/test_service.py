import unittest
from unittest.mock import patch

from quant_platform.service import (
    get_sector_screen,
    get_sector_snapshot,
    get_stock_analysis,
    run_stock_backtest,
)


class ServiceTests(unittest.TestCase):
    @patch("quant_platform.service.fetch_stock_history")
    @patch("quant_platform.service.create_session")
    def test_reuses_provided_session(
        self,
        create_session_mock,
        fetch_stock_history_mock,
    ) -> None:
        stock_data = {"symbol": "sh600519", "code": "600519", "history": []}
        fetch_stock_history_mock.return_value = stock_data
        session = object()

        with patch("quant_platform.service.analyze_stock_history") as analyze_mock:
            result = get_stock_analysis("600519", session=session)

        create_session_mock.assert_not_called()
        fetch_stock_history_mock.assert_called_once()
        self.assertIs(fetch_stock_history_mock.call_args.kwargs["session"], session)
        self.assertIn("stock", result)

    @patch("quant_platform.service.fetch_sector_snapshot")
    @patch("quant_platform.service.create_session")
    def test_sector_reuses_provided_session(
        self,
        create_session_mock,
        fetch_sector_snapshot_mock,
    ) -> None:
        snapshot = {"sector": {}, "members": []}
        fetch_sector_snapshot_mock.return_value = snapshot
        session = object()

        result = get_sector_snapshot("人工智能", session=session)

        create_session_mock.assert_not_called()
        self.assertIs(fetch_sector_snapshot_mock.call_args.args[0], session)
        self.assertEqual(result, snapshot)

    @patch("quant_platform.service.rank_members")
    @patch("quant_platform.service.fetch_sector_snapshot")
    @patch("quant_platform.service.create_session")
    def test_sector_screen_returns_service_payload(
        self,
        create_session_mock,
        fetch_sector_snapshot_mock,
        rank_members_mock,
    ) -> None:
        session = object()
        snapshot = {"sector": {"board_code": "BK0579"}, "members": [{"stock_code": "600519"}]}
        fetch_sector_snapshot_mock.return_value = snapshot
        rank_members_mock.return_value = [{"stock_code": "600519"}]

        result = get_sector_screen("人工智能", limit=2, session=session)

        create_session_mock.assert_not_called()
        self.assertIs(fetch_sector_snapshot_mock.call_args.args[0], session)
        self.assertEqual(result["member_count"], 1)
        self.assertEqual(result["members"], [{"stock_code": "600519"}])

    @patch("quant_platform.service.backtest_ma_cross")
    @patch("quant_platform.service.fetch_stock_history")
    @patch("quant_platform.service.create_session")
    def test_backtest_reuses_provided_session(
        self,
        create_session_mock,
        fetch_stock_history_mock,
        backtest_mock,
    ) -> None:
        stock_data = {"symbol": "sh600519", "code": "600519", "history": []}
        fetch_stock_history_mock.return_value = stock_data
        backtest_mock.return_value = {"total_return": 0.0}
        session = object()

        result = run_stock_backtest("600519", session=session)

        create_session_mock.assert_not_called()
        self.assertIs(fetch_stock_history_mock.call_args.kwargs["session"], session)
        self.assertIn("backtest", result)


if __name__ == "__main__":
    unittest.main()
