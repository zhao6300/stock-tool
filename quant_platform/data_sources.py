"""Public market data adapters. Each function returns plain dictionaries."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any
import time

import requests
import re


SEARCH_URL = "https://searchapi.eastmoney.com/api/suggest/get"
QUOTE_URL = "https://push2delay.eastmoney.com/api/qt/stock/get"
MEMBERS_URL = "https://push2delay.eastmoney.com/api/qt/clist/get"
STOCK_HISTORY_URL = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
DEFAULT_SECTORS = ["人工智能", "算力概念", "国产软件", "云计算", "半导体设备"]
TOKEN = "D43BF722C8E33BDC906FB84D85E326E8"


def default_range(end_date: str | None = None, days: int = 365) -> tuple[str, str]:
    end = date.fromisoformat(end_date) if end_date else date.today()
    start = end - timedelta(days=days)
    return start.isoformat(), end.isoformat()


def parse_date_range(
    start_date: str | None = None,
    end_date: str | None = None,
    days: int = 365,
) -> tuple[str, str]:
    if start_date and end_date:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        if start > end:
            raise ValueError("start_date must be on or before end_date")
        return start.isoformat(), end.isoformat()
    if start_date and not end_date:
        start = date.fromisoformat(start_date)
        end = date.today()
        if start > end:
            raise ValueError("start_date must be on or before end_date")
        return start.isoformat(), end.isoformat()
    return default_range(end_date, days)


def resilient_get(
    session: requests.Session,
    url: str,
    params: dict[str, Any],
    retries: int = 3,
    retry_backoff_seconds: float = 0.25,
):
    if retries <= 0:
        raise ValueError("retries must be positive")
    if retry_backoff_seconds < 0:
        raise ValueError("retry_backoff_seconds must be non-negative")
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            response = session.get(url, params=params, timeout=8)
            response.raise_for_status()
            return response
        except requests.RequestException as error:
            last_error = error
            if attempt < retries - 1:
                time.sleep(retry_backoff_seconds * (2**attempt))
    if last_error is not None:
        raise RuntimeError(f"Request failed: {url}") from last_error
    raise RuntimeError(f"Request loop exited unexpectedly: {url}")


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/128.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
        }
    )
    return session


def validate_stock_code(raw_code: str) -> str:
    code = raw_code.strip().lower()
    if code[:2] in {"sh", "sz", "bj"} and len(code) == 8 and code[2:].isdigit():
        return code
    if not re.fullmatch(r"\d{6}", code):
        raise ValueError(f" Unsupported stock code: {raw_code}")
    if code.startswith("6"):
        return f"sh{code}"
    if code.startswith(("0", "2", "3")):
        return f"sz{code}"
    if code.startswith(("4", "8")):
        return f"bj{code}"
    raise ValueError(f" Unsupported stock code: {raw_code}")


def stock_symbol(raw_code: str) -> str:
    code = validate_stock_code(raw_code)
    if code.startswith(("sh", "sz", "bj")):
        return code
    return f"sh{code}"


def fetch_stock_history(
    session: requests.Session,
    raw_code: str,
    end_date: str | None = None,
    days: int = 365,
    start_date: str | None = None,
) -> dict[str, object]:
    symbol = stock_symbol(raw_code)
    start_date, resolved_end_date = parse_date_range(start_date, end_date, days)
    response = resilient_get(
        session,
        STOCK_HISTORY_URL,
        {"param": f"{symbol},day,{start_date},{resolved_end_date},2000,qfq"},
    )
    payload = response.json()
    data = payload.get("data")
    stock_data = data.get(symbol) if isinstance(data, dict) else None
    stock_data = stock_data or {}
    rows = stock_data.get("qfqday") or stock_data.get("day") or []
    history: list[dict[str, float | str]] = []
    for row in rows:
        try:
            history.append(
                {
                    "date": row[0],
                    "open": float(row[1]),
                    "close": float(row[2]),
                    "high": float(row[3]),
                    "low": float(row[4]),
                    "volume": float(row[5]),
                }
            )
        except (IndexError, TypeError, ValueError):
            continue
    return {"symbol": symbol, "code": raw_code, "history": history}


def search_sector(session: requests.Session, name: str) -> dict[str, str] | None:
    response = resilient_get(
        session,
        SEARCH_URL,
        {"input": name, "type": 14, "token": TOKEN, "count": 20},
    )
    records = response.json().get("QuotationCodeTable", {}).get("Data") or []
    for record in records:
        if record.get("Name") == name and record.get("Code", "").startswith("BK"):
            return {"code": record["Code"], "name": record["Name"]}
    for record in records:
        if record.get("Code", "").startswith("BK"):
            return {"code": record["Code"], "name": record["Name"]}
    return None


def fetch_board_snapshot(session: requests.Session, sector: dict[str, str]) -> dict[str, object]:
    quote_response = resilient_get(
        session,
        QUOTE_URL,
        {"secid": f"90.{sector['code']}", "fields": "f57,f58,f43,f60,f170", "fltt": 2, "invt": 2},
    )
    quote = quote_response.json().get("data") or {}
    quote.update({"board_code": sector["code"], "board_name": sector["name"]})
    return quote


def fetch_board_members(session: requests.Session, sector: dict[str, str]) -> list[dict[str, object]]:
    page = 1
    members = []
    while True:
        response = resilient_get(
            session,
            MEMBERS_URL,
            {
                "pn": page,
                "pz": 100,
                "po": 1,
                "np": 1,
                "fltt": 2,
                "invt": 2,
                "fid": "f3",
                "fs": f"b:{sector['code']}",
                "fields": "f12,f14,f3,f20,f62",
            },
        )
        payload = response.json().get("data") or {}
        raw_members = payload.get("diff") or []
        for row in raw_members:
            members.append(
                {
                    "board_name": sector["name"],
                    "stock_code": row.get("f12"),
                    "stock_name": row.get("f14"),
                    "change_percent": row.get("f3"),
                    "market_cap": row.get("f20"),
                    "main_net_inflow": row.get("f62"),
                }
            )
        total = int(payload.get("total", 0) or 0)
        if not raw_members or len(members) >= total:
            break
        page += 1
    return members


def fetch_sector_snapshot(session: requests.Session, name: str) -> dict[str, object]:
    sector = search_sector(session, name)
    if sector is None:
        raise ValueError(f"未找到板块：{name}")
    return {
        "sector": fetch_board_snapshot(session, sector),
        "members": fetch_board_members(session, sector),
    }
