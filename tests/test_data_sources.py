import unittest

from quant_platform.data_sources import (
    default_range,
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
