# **RawMD Directory Manager Case Study**

> Visit the Mathema Option Pricing System!
[![Visit the Mathema Option Pricing System](../pic/mathema.png)](https://fxo.mathema.com.cn)

Directory mode: point to a folder containing `MCP_MARKET_DATA_YYYYMMDD.json` files.

> **Ready to run**: Download the [TC31–TC46 example pack](/download/MCP-TC31-46-LiveStoreRawMD.zip) (all workbooks plus shared `data/`). Unzip and open the xlsx under `en`. A single workbook will not run unless you place the pack's `data` folder next to it.

[Download MCP-TC32-RawMarketManager.xlsx](./MCP-TC32-RawMarketManager.xlsx)

## **Object chain**

`McpRawMarketManager("data/market_data")` → `rawmdGetYieldCurve2(mgr, id, val_date)` → `YieldCurve2ZeroRate`

## **Key functions**

| Function | Description |
|----------|-------------|
| [McpRawMarketManager](/latest/api/rawmarketdata.html) | Directory manager |
| [rawmdGetYieldCurve2](/latest/api/rawmarketdata.html) | YieldCurve2 by date |
| [rawmdAvailableDates](/latest/api/rawmarketdata.html) | Available dates |

See `example/market_data/rawmd_demo.py`.
