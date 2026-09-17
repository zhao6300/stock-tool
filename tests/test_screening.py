import unittest

from quant_platform.screening import rank_members


class ScreeningTests(unittest.TestCase):
    def test_rank_members(self) -> None:
        members = [
            {"stock_code": "A", "change_percent": 1.0},
            {"stock_code": "B", "change_percent": None},
            {"stock_code": "C", "change_percent": 3.0},
            {"stock_code": "D", "change_percent": 2.0},
        ]
        ranked = rank_members(members, limit=2)
        self.assertEqual([member["stock_code"] for member in ranked], ["C", "D"])

    def test_rank_members_empty(self) -> None:
        self.assertEqual(rank_members([], limit=3), [])
