# **JsonReader Read-Only Case Study**

> Visit the Mathema Option Pricing System!
[![Visit the Mathema Option Pricing System](../pic/mathema.png)](https://fxo.mathema.com.cn)

Read-only single-file load; same JSON as LiveStore; **no patch**.

[Download MCP-TC34-MarketDataJsonReader.xlsx](./MCP-TC34-MarketDataJsonReader.xlsx)

## **Object chain**

`McpMarketDataJsonReader(Config!B2)` → `mdjsonGetYieldCurve2` → `YieldCurve2ZeroRate`

## **Key functions**

| Function | Description |
|----------|-------------|
| [McpMarketDataJsonReader](/latest/api/rawmarketdata.html) | Read-only reader |
| [mdjsonGetYieldCurve2](/latest/api/rawmarketdata.html) | Get YieldCurve2 |

See `example/market_data/json_reader_demo.py`.

## **vs TC31**

| | LiveStore | JsonReader |
|--|-----------|------------|
| patch | yes | **no** |
