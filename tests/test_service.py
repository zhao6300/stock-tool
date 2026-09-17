import unittest
from unittest.mock import patch

from quant_platform.service import get_stock_analysis


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


if __name__ == "__main__":
    unittest.main()
