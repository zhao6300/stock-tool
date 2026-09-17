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

## 新版本设计

新增了 `quant_platform` 包，借鉴常见量化平台的分层思路：

- `quant_platform/data_sources.py`：数据层，负责外部行情适配、重试和接口字段映射。
- `quant_platform/metrics.py`：纯数学基础工具。
- `quant_platform/indicators.py`：基于基础工具的组合指标。
- `quant_platform/analysis.py`：分析层，只做纯函数计算，便于测试。
- `quant_platform/screening.py`：纯函数筛选/排名。
- `quant_platform/service.py`：业务编排，供 CLI、API、调度器复用。
- `quant_platform/cli.py`：展示层，负责命令行输入输出。

## 新版运行

单只股票历史分析：

```bash
python3 -m quant_platform.cli stock 600519 --days 30
```

板块实盘快照：

```bash
python3 -m quant_platform.cli sector 人工智能 算力概念
python3 -m quant_platform.cli sector 人工智能 --top 10
```

推荐使用更紧凑的模块入口：

```bash
python3 -m quant_platform stock 600519 --days 30
```

单只股票风险摘要：

```bash
python3 -m quant_platform stock 600519 --days 90 --format text
```

均线交叉回测：

```bash
python3 -m quant_platform backtest 600519 --days 180
python3 -m quant_platform backtest 600519 --fast 20 --slow 60 --cost 0.0002
```

回测结果会同时展示策略表现和买入持有基准，便于判断策略是否优于简单持有。

## 测试

```bash
python3 -m unittest discover -s tests -v
```
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
