import unittest
from unittest.mock import Mock, patch
import requests

from quant_platform import data_sources

from quant_platform.data_sources import (
    default_range,
    fetch_board_members,
    fetch_stock_history,
    resilient_get,
    search_sector,
    parse_date_range,
    stock_symbol,
    validate_stock_code,
)


class DataSourceTests(unittest.TestCase):
    def test_default_range(self) -> None:
        start, end = default_range("2025-01-02", 1)
        self.assertEqual(start, "2025-01-01")
        self.assertEqual(end, "2025-01-02")

    def test_stock_symbol(self) -> None:
        self.assertEqual(stock_symbol("600519"), "sh600519")
        self.assertEqual(stock_symbol("002230"), "sz002230")
        self.assertEqual(stock_symbol("830001"), "bj830001")

    def test_validate_stock_code(self) -> None:
        with self.assertRaises(ValueError):
            validate_stock_code("abc123")
        with self.assertRaises(ValueError):
            validate_stock_code("12345678")

    def test_parse_date_range(self) -> None:
        start, end = parse_date_range("2025-01-01", "2025-01-03", 10)
        self.assertEqual(start, "2025-01-01")
        self.assertEqual(end, "2025-01-03")

    def test_parse_date_range_defaults(self) -> None:
        start, end = parse_date_range(None, "2026-01-02", 1)
        self.assertEqual(start, "2026-01-01")
        self.assertEqual(end, "2026-01-02")

    def test_parse_date_range_start_only(self) -> None:
        start, end = parse_date_range("2026-01-01", None, 365)
        self.assertEqual(start, "2026-01-01")

    def test_resilient_get_returns_after_retry(self) -> None:
        failed_response = Mock()
        failed_response.raise_for_status.side_effect = requests.HTTPError("temporary")
        success_response = Mock()
        session = Mock()
        session.get.side_effect = [failed_response, failed_response, success_response]

        response = resilient_get(session, "https://example.com", {"a": 1})

        self.assertEqual(response, success_response)
        self.assertEqual(session.get.call_count, 3)
        self.assertEqual(session.get.call_args.kwargs["timeout"], 8)

    def test_resilient_get_raises_runtime_error(self) -> None:
        failed_response = Mock()
        failed_response.raise_for_status.side_effect = requests.HTTPError("bad request")
        session = Mock()
        session.get.return_value = failed_response

        with self.assertRaises(RuntimeError) as context:
            resilient_get(session, "https://example.com", {"a": 1}, retries=2)

        self.assertEqual(session.get.call_count, 2)
        self.assertIn("https://example.com", str(context.exception))

    @patch("quant_platform.data_sources.time.sleep")
    def test_resilient_get_uses_exponential_backoff(self, sleep_mock) -> None:
        failed_response = Mock()
        failed_response.raise_for_status.side_effect = requests.ConnectionError("network")
        session = Mock()
        session.get.return_value = failed_response

        with self.assertRaises(RuntimeError):
            resilient_get(session, "https://example.com", {}, retries=3, retry_backoff_seconds=0.25)

        self.assertEqual([call.args[0] for call in sleep_mock.call_args_list], [0.25, 0.5])

    def test_fetch_stock_history_maps_qfq_rows(self) -> None:
        payload = {
            "data": {
                "sh600519": {
                    "qfqday": [
                        ["2026-01-02", "1800", "1810", "1820", "1790", "1000"],
                        ["bad", "2", "3"],
                    ],
                    "day": [["ignored"]],
                },
                "wrong_symbol": {"qfqday": [["bad"]]},
            },
        }
        response = Mock()
        response.json.return_value = payload
        session = Mock()
        session.get.return_value = response

        result = fetch_stock_history(session, "600519", start_date="2026-01-01", end_date="2026-01-02")

        self.assertEqual(result["symbol"], "sh600519")
        self.assertEqual(
            result["history"],
            [
                {
                    "date": "2026-01-02",
                    "open": 1800.0,
                    "close": 1810.0,
                    "high": 1820.0,
                    "low": 1790.0,
                    "volume": 1000.0,
                }
            ],
        )

    def test_search_sector_prefers_exact_name(self) -> None:
        payload = {
            "QuotationCodeTable": {
                "Data": [
                    {"Name": "人工智能相似", "Code": "BK1111"},
                    {"Name": "人工智能", "Code": "BK0579"},
                ]
            }
        }
        response = Mock()
        response.json.return_value = payload
        session = Mock()
        session.get.return_value = response

        result = search_sector(session, "人工智能")

        self.assertEqual(result, {"code": "BK0579", "name": "人工智能"})
        self.assertEqual(session.get.call_args.args[0], data_sources.SEARCH_URL)

    def test_fetch_board_members_paginates_until_total(self) -> None:
        pages = [
            {"data": {"total": 3, "diff": [{"f12": "600519", "f14": "贵州茅台", "f3": 1.0}]}},
            {
                "data": {
                    "total": 3,
                    "diff": [
                        {"f12": "002230", "f14": "科大讯飞", "f3": -2.0},
                        {"f12": "000001", "f14": "平安银行", "f3": 3.0},
                    ],
                }
            },
        ]
        responses = []
        for payload in pages:
            response = Mock()
            response.json.return_value = payload
            responses.append(response)
        session = Mock()
        session.get.side_effect = responses

        members = fetch_board_members(session, {"code": "BK0579", "name": "人工智能"})

        self.assertEqual(session.get.call_count, 2)
        self.assertEqual([member["stock_code"] for member in members], ["600519", "002230", "000001"])
        self.assertEqual(session.get.call_args_list[0].kwargs["params"]["pn"], 1)
        self.assertEqual(session.get.call_args_list[1].kwargs["params"]["pn"], 2)
