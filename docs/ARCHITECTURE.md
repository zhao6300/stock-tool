# Architecture

The toolkit is intentionally split into three layers.

## Data layer

`quant_platform/data_sources.py` adapts public endpoints into a stable Python dictionary format. It isolates:

- retry/backoff
- provider quirks
- stock prefix mapping
- sector search and member snapshots

## Analysis layer

`quant_platform/analysis.py` contains only pure functions so metrics can be unit tested without network access.

`quant_platform/backtest.py` contains pure strategy evaluation functions.

`quant_platform/screening.py` contains ranking and screening helpers without network or CLI concerns.

`quant_platform/metrics.py` holds reusable math primitives.
`quant_platform/indicators.py` composes those primitives into market indicators.

Current metrics include:

- returns
- annualized volatility
- maximum drawdown
- moving averages
- volume averages
- short/medium trend classification
- Sharpe / Sortino ratio
- momentum

Reusable primitives include:

- returns
- volatility
- maximum drawdown
- moving averages
- RSI / MACD / Bollinger Bands

## CLI layer
- `quant_platform/service.py` is the orchestration boundary for future API and scheduler integration.

`quant_platform/cli.py` only parses arguments and displays results. It does not contain financial calculations or network logic.
## Pure math layer

`quant_platform/metrics.py` uses only pure functions so metrics are deterministic and easy to test.

`quant_platform/indicators.py` composes market analytics from those primitives.

`quant_platform/risk.py` provides additional downside and systematic-risk measures such as Value-at-Risk, Expected Shortfall, beta, and alpha.
