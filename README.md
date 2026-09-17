# 中国 AI 板块行情采集脚本

采集东方财富公开接口中的 A 股板块指数、涨跌幅和成分股行情。

## 运行

```bash
pip install requests
python3 ai_market_data.py -o ai_market_data
```

指定板块：

```bash
python3 ai_market_data.py -s 人工智能 算力概念 -o ai_market_data
```

## 生成文件

- `sector_quotes.csv`：板块代码、板块名称、最新指数、昨收、涨跌幅
- `members_BK*.csv`：对应板块成分股代码、名称、涨跌幅、市值、主力净流入

> 提示：脚本使用的是 East Money 延时行情域名，适合观察和示例用途，不适合高频交易。
## 单只股票历史分析

```bash
python3 ai_market_data.py --print --stock 002230
python3 ai_market_data.py --print --stock 002230 --start 2025-01-01 --end 2026-09-17
```

脚本会基于前复权日 K 线输出：

- 最新收盘价与区间涨跌幅
- 年化收益率和年化波动率
- 最大回撤
- 5 / 20 / 60 日均线
- 5 / 20 日均量
- 短中期趋势判断

数据源使用腾讯财经公开接口，适合观察与研究，不适合交易决策。
