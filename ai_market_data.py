#!/usr/bin/env python3

"""Fetch and export live quotes for China A-share AI-related sectors."""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path
from typing import Iterable

import requests


SEARCH_URL = "https://searchapi.eastmoney.com/api/suggest/get"
QUOTE_URL = "https://push2delay.eastmoney.com/api/qt/stock/get"
MEMBERS_URL = "https://push2delay.eastmoney.com/api/qt/clist/get"
DEFAULT_SECTORS = ["人工智能", "算力概念", "国产软件", "云计算", "半导体设备"]
TOKEN = "D43BF722C8E33BDC906FB84D85E326E8"


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/128.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
        }
    )
    return session


def resilient_get(session, url, params, retries=3):
    last_error = None
    for attempt in range(retries):
        try:
            response = session.get(url, params=params, timeout=8)
            response.raise_for_status()
            return response
        except requests.RequestException as error:
            last_error = error
            if attempt < retries - 1:
                sleep_seconds = 1.0 * (attempt + 1)
                print(
                    f"请求重试 {attempt + 1}: {error!r}，等待 {sleep_seconds:.1f} 秒",
                    file=sys.stderr,
                )
                time.sleep(sleep_seconds)
    raise RuntimeError(f"无法请求 {url}") from last_error


def search_sector_by_name(session, name):
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


def fetch_board_quote(session, sector):
    response = resilient_get(
        session,
        QUOTE_URL,
        {
            "secid": f"90.{sector['code']}",
            "fields": "f57,f58,f43,f60,f170",
            "fltt": 2,
            "invt": 2,
        },
    )
    data = response.json().get("data")
    if not isinstance(data, dict):
        raise RuntimeError(f"板块 {sector['code']} 没有行情数据")
    return data


def fetch_board_members(session, sector):
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
        if len(members) >= total or not raw_members:
            break
        page += 1
    return members


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as file_handler:
        writer = csv.DictWriter(file_handler, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="采集中国 A 股 AI 相关板块行情。")
    parser.add_argument("-s", "--sectors", nargs="+", default=DEFAULT_SECTORS)
    parser.add_argument("-o", "--output-dir", default="ai_market_data")
    parser.add_argument("-p", "--print", action="store_true", help="直接打印到屏幕而不写入 CSV")
    args = parser.parse_args()

    if getattr(args, "print"):
        session = create_session()
        for sector_name in args.sectors:
            sector = search_sector_by_name(session, sector_name)
            if not sector:
                print(f"未找到板块：{sector_name}", file=sys.stderr)
                continue
            quote = fetch_board_quote(session, sector)
            members = fetch_board_members(session, sector)
            print(sector)
            print("板块行情：", quote)
            print("成分股前 10：")
            for row in members[:10]:
                print(row)
            print(f"板块 {sector['name']} 共有 {len(members)} 只成分股")
            print()
        return

    session = create_session()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    all_quotes = []

    for sector_name in args.sectors:
        sector = search_sector_by_name(session, sector_name)
        if not sector:
            print(f"未找到板块：{sector_name}", file=sys.stderr)
            continue
        quote = fetch_board_quote(session, sector)
        quote.update({"board_code": sector["code"], "board_name": sector["name"]})
        members = fetch_board_members(session, sector)
        member_path = output_dir / f"members_{sector['code']}.csv"
        write_csv(
            member_path,
            members,
            ["board_name", "stock_code", "stock_name", "change_percent", "market_cap", "main_net_inflow"],
        )
        all_quotes.append(quote)
        print(f"{sector['name']}: {len(members)} 只成分股，已保存到 {member_path}")

    quote_path = output_dir / "sector_quotes.csv"
    write_csv(quote_path, all_quotes, ["board_code", "board_name", "f43", "f60", "f170"])
    print(f"完成 {len(all_quotes)} 个板块，汇总文件：{quote_path}")


if __name__ == "__main__":
    main()
