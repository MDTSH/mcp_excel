# **FR007 SwapCurve RawMD Case Study**

> Visit the Mathema Option Pricing System for foreign exchange options and structured product valuation!
[![Visit the Mathema Option Pricing System](../pic/mathema.png)](https://fxo.mathema.com.cn)

Load FR007 swap curve from standard JSON by valuation date, then read with `SwapCurveZeroRate`.

## **Overview**

Load the FR007 swap curve from standard JSON by valuation date: `McpRawMarketManager` → `rawmdGetSwapCurve("CNY_SWAP_FR007_BGN")` → `SwapCurveZeroRate` / `SwapCurveDiscountFactor`.

Data: `data/market_data/MCP_MARKET_DATA_20260626.json`, valuation date 2026-06-26. Key sheets: `Config` (paths / date / Manager / curve_id), `RawMD` (object + tenor zeros and DFs). After F9 the curve cell should be `McpSwapCurve@n` with values on each tenor.

[Download MCP-TC39-FR007SwapCurveRawMD.xlsx](./MCP-TC39-FR007SwapCurveRawMD.xlsx)

## **Object chain**

1. `=McpRawMarketManager("data/market_data")`  
2. `=rawmdGetSwapCurve(mgr,"CNY_SWAP_FR007_BGN",val_date)`  
3. `=SwapCurveZeroRate(curve, date)` / `SwapCurveDiscountFactor`

MarketDataRoot: `data/market_data` (relative). Valuation date 2026-06-26.

## **Key functions**

| Function | Description |
|----------|-------------|
| [McpRawMarketManager](/latest/api/rawmarketdata.html) | Directory manager |
| [rawmdGetSwapCurve](/latest/api/rawmarketdata.html) | SwapCurve object |
| SwapCurveZeroRate | Zero rate |

## **Python example**

See `example/market_data/fr007_rawmd_demo.py`.

## **Troubleshooting**

- Directory must contain `MCP_MARKET_DATA_20260626.json`
- `#NAME?`: register `mcp_raw_market_data` and Reload PyXLL
