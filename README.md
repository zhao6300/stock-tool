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
