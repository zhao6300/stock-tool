"""CLI layer for readers and analysis users."""

from __future__ import annotations

import argparse
import json
from typing import Any

from .screening import rank_members
from .service import get_sector_snapshot, get_stock_analysis, run_stock_backtest
from .data_sources import DEFAULT_SECTORS, create_session


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def run_stock(args: argparse.Namespace) -> None:
    session = create_session()
    for code in args.code:
        result = get_stock_analysis(
            code,
            start_date=args.start,
            end_date=args.end,
            days=args.days,
            session=session,
        )
        if args.format == "json":
            print_json(result)
        else:
            analysis = result["analysis"]
            print(f"symbol={analysis['symbol']}")
            print(f"period={analysis['start_date']}..{analysis['end_date']}")
            print(f"close={analysis['latest_close']:.2f}")
            print(f"period_return={analysis['period_return']:.2%}")
            print(f"annualized_return={analysis['annualized_return']:.2%}")
            print(f"annualized_volatility={analysis['annualized_volatility']:.2%}")
            print(f"max_drawdown={analysis['max_drawdown']:.2%}")
            print(f"sharpe_ratio={analysis['sharpe_ratio']:.2f}")
            print(f"sortino_ratio={analysis['sortino_ratio']:.2f}")
            print(f"value_at_risk_95={analysis['value_at_risk_95']:.2%}")
            print(f"expected_shortfall_95={analysis['expected_shortfall_95']:.2%}")
            print(f"trend={analysis['trend']}")


def run_sector(args: argparse.Namespace) -> None:
    session = create_session()
    for name in args.names:
        snapshot = get_sector_snapshot(name, session=session)
        members = rank_members(snapshot["members"], limit=args.top)
        payload = {
            "sector": snapshot["sector"],
            "member_count": len(snapshot["members"]),
            "movers": members,
        }
        if args.format == "json":
            print_json(payload)
        else:
            quote = payload["sector"]
            print(f"sector={quote['board_name']}")
            print(f"code={quote['board_code']}")
            print(f"index={quote.get('f43')}")
            print(f"change_percent={quote.get('f170')}")
            print(f"member_count={payload['member_count']}")
            for member in members:
                print(f"{member['stock_code']} {member['stock_name']} {member['change_percent']}")


def run_backtest(args: argparse.Namespace) -> None:
    result = run_stock_backtest(
        args.code,
        start_date=args.start,
        end_date=args.end,
        days=args.days,
        fast=args.fast,
        slow=args.slow,
    initial_capital=args.capital,
    transaction_cost_rate=args.cost,
    session=session,
)
    if args.format == "json":
        print_json(result)
    else:
        backtest = result["backtest"]
        print(f"symbol={result['stock']['symbol']}")
        print(f"strategy=ma_cross_fast_{args.fast}_slow_{args.slow}")
        print(f"initial_capital={backtest['initial_capital']:.2f}")
        print(f"final_equity={backtest['final_equity']:.2f}")
        print(f"total_return={backtest['total_return']:.2%}")
        print(f"annualized_return={backtest['annualized_return']:.2%}")
        print(f"annualized_volatility={backtest['annualized_volatility']:.2%}")
        print(f"sharpe_ratio={backtest['sharpe_ratio']:.2f}")
        print(f"sortino_ratio={backtest['sortino_ratio']:.2f}")
        print(f"max_drawdown={backtest['max_drawdown']:.2%}")
        print(f"transaction_costs={backtest['transaction_costs']:.2f}")
        print(f"trade_count={backtest['trade_count']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="quant-platform",
        description="分层的 A 股市场数据和分析工具。",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    stock = subparsers.add_parser("stock", help="单只股票历史分析")
    stock.add_argument("code", nargs="+")
    stock.add_argument("--start", help="起始日期 YYYY-MM-DD；可选")
    stock.add_argument("--end", help="结束日期 YYYY-MM-DD；默认今天")
    stock.add_argument("--days", type=int, default=365, help="回看自然日数，默认 365")
    stock.add_argument("--format", choices=["text", "json"], default="text")
    stock.set_defaults(handler=run_stock)

    sector = subparsers.add_parser("sector", help="板块实盘快照")
    sector.add_argument("names", nargs="*", default=DEFAULT_SECTORS)
    sector.add_argument("--top", type=int, default=10, help="输出当天涨跌幅前 N")
    sector.add_argument("--format", choices=["text", "json"], default="text")
    sector.set_defaults(handler=run_sector)
    backtest = subparsers.add_parser("backtest", help="单只股票均线交叉回测")
    backtest.add_argument("code")
    backtest.add_argument("--start")
    backtest.add_argument("--end")
    backtest.add_argument("--days", type=int, default=365)
    backtest.add_argument("--fast", type=int, default=20)
    backtest.add_argument("--slow", type=int, default=60)
    backtest.add_argument("--capital", type=float, default=100_000.0)
    backtest.add_argument("--cost", type=float, default=0.0)
    backtest.add_argument("--format", choices=["text", "json"], default="text")
    backtest.set_defaults(handler=run_backtest)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
