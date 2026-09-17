#!/usr/bin/env python3

"""Fetch and export live quotes for China A-share AI-related sectors."""

from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import date, timedelta
import math
from pathlib import Path
from typing import Iterable

import requests


SEARCH_URL = "https://searchapi.eastmoney.com/api/suggest/get"
QUOTE_URL = "https://push2delay.eastmoney.com/api/qt/stock/get"
MEMBERS_URL = "https://push2delay.eastmoney.com/api/qt/clist/get"
STOCK_HISTORY_URL = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
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


def stock_symbol(code):
    code = code.strip().lower()
    if code[:2] in {"sh", "sz", "bj"}:
        return code
    if code.startswith("6") or code.startswith("9"):
        return f"sh{code}"
    if code.startswith(("0", "2", "3")):
        return f"sz{code}"
    if code.startswith(("4", "8")):
        return f"bj{code}"
    raise ValueError(f"无法识别股票代码：{code}")


def fetch_stock_history(session, raw_code, start_date, end_date):
    symbol = stock_symbol(raw_code)
    response = resilient_get(
        session,
        STOCK_HISTORY_URL,
        {
            "param": f"{symbol},day,{start_date},{end_date},2000,qfq",
        },
    )
    payload = response.json()
    if payload.get("code", 1) != 0:
        raise RuntimeError(f"获取 {symbol} 历史数据失败：{payload}")
    data = payload.get("data")
    stock_data = data.get(symbol) if isinstance(data, dict) else None
    stock_data = stock_data or {}
    records = stock_data.get("qfqday") or stock_data.get("day") or []
    history = []
    for row in records:
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


def percent_returns(closes):
    if len(closes) < 2:
        return []
    return [current / previous - 1 for previous, current in zip(closes[:-1], closes[1:])]


def mean(values):
    return sum(values) / len(values)


def standard_deviation(values):
    if len(values) < 2:
        return 0.0
    center = mean(values)
    return math.sqrt(sum((value - center) ** 2 for value in values) / (len(values) - 1))


def maximum_drawdown(closes):
    peak = closes[0]
    drawdown = 0.0
    for close in closes:
        peak = max(peak, close)
        drawdown = min(drawdown, close / peak - 1 if peak > 0 else 0)
    return drawdown


def trailing_mean(values, window):
    if len(values) < window:
        return None
    return mean(values[-window:])


def analyze_stock_history(stock_data):
    history = stock_data["history"]
    if not history:
        raise RuntimeError(f"没有可分析的历史数据：{stock_data['symbol']}")
    closes = [row["close"] for row in history]
    returns = percent_returns(closes)
    latest_close = closes[-1]
    first_close = closes[0]
    annualized_return = (
        (latest_close / first_close) ** (252 / len(returns)) - 1
        if first_close > 0 and len(returns) > 0
        else 0.0
    )
    annualized_volatility = standard_deviation(returns) * math.sqrt(252)
    ma5 = trailing_mean(closes, 5)
    ma20 = trailing_mean(closes, 20)
    ma60 = trailing_mean(closes, 60)
    if ma20 is None:
        trend = "样本不足，无法计算 20 日均线"
    elif ma60 is None:
        trend = "样本不足，无法计算 60 日均线"
    elif latest_close > ma20 and ma20 > ma60:
        trend = "短中期趋势向上"
    elif latest_close < ma20 and ma20 < ma60:
        trend = "短中期趋势向下"
    else:
        trend = "短期趋势震荡"
    volume_ma5 = trailing_mean([row["volume"] for row in history], 5)
    volume_ma20 = trailing_mean([row["volume"] for row in history], 20)
    return {
        "symbol": stock_data["symbol"],
        "start_date": history[0]["date"],
        "end_date": history[-1]["date"],
        "observations": len(history),
        "start_close": first_close,
        "latest_close": latest_close,
        "period_return": latest_close / first_close - 1,
        "annualized_return": annualized_return,
        "annualized_volatility": annualized_volatility,
        "max_drawdown": maximum_drawdown(closes),
        "ma5": ma5,
        "ma20": ma20,
        "ma60": ma60,
        "volume_ma5": volume_ma5,
        "volume_ma20": volume_ma20,
        "trend": trend,
    }


def print_stock_analysis(analysis):
    print(f"股票：{analysis['symbol']}")
    print(f"区间：{analysis['start_date']} → {analysis['end_date']}")
    print(f"样本数：{analysis['observations']}")
    print(f"起收盘价：{analysis['start_close']:.2f}")
    print(f"最新收盘价：{analysis['latest_close']:.2f}")
    print(f"区间收益率：{analysis['period_return']:.2%}")
    print(f"年化收益率：{analysis['annualized_return']:.2%}")
    print(f"年化波动率：{analysis['annualized_volatility']:.2%}")
    print(f"最大回撤：{analysis['max_drawdown']:.2%}")
    for name in ("ma5", "ma20", "ma60"):
        value = analysis[name]
        if value is not None:
            print(f"{name.upper()}：{value:.2f}")
    if analysis["volume_ma5"] is not None:
        print(f"5日均值量：{analysis['volume_ma5']:.0f}")
    if analysis["volume_ma20"] is not None:
        print(f"20日均值量：{analysis['volume_ma20']:.0f}")
    print(f"趋势判断：{analysis['trend']}")


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as file_handler:
        writer = csv.DictWriter(file_handler, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="采集中国 A 股 AI 相关板块行情。")
    parser.add_argument("-s", "--sectors", nargs="+", default=DEFAULT_SECTORS)
    parser.add_argument("-c", "--stock", nargs="+", default=[], help="股票代码，如 002230 或 600519")
    parser.add_argument("--start", default=None, help="历史数据起始日，YYYY-MM-DD")
    parser.add_argument("--end", default=None, help="历史数据结束日，YYYY-MM-DD")
    parser.add_argument("-o", "--output-dir", default="ai_market_data")
    parser.add_argument("-p", "--print", action="store_true", help="直接打印到屏幕而不写入 CSV")
    args = parser.parse_args()

    end_date = args.end or date.today().isoformat()
    start_date = args.start or (date.today() - timedelta(days=365)).isoformat()

    if getattr(args, "print"):
        session = create_session()
        if args.stock:
            for code in args.stock:
                stock_data = fetch_stock_history(session, code, start_date, end_date)
                analysis = analyze_stock_history(stock_data)
                print_stock_analysis(analysis)
                print()
            return
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
