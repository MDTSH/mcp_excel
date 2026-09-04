# **CreditCurve Case**


> Visit the Mathema Option Pricing System for FX options and structured-product valuation!
[![Visit the Mathema Option Pricing System](../pic/mathema.png)](https://fxo.mathema.com.cn)

Load a credit curve from standard JSON, then read with existing `CreditCurveHazardRate` / `CreditCurveDefaultProbability`.

**What it does:** LiveStore / RawMD / JsonReader sheets use the same `CNY_CREDIT_CFETS` (spreads in BP, depends on `CNYDEPO`). Use the C++ Manager / Store path.

> **Ready to run**: Download the [TC31–TC46 example pack](/download/MCP-TC31-46-LiveStoreRawMD.zip) (all workbooks plus shared `data/`). Unzip and open the xlsx under `en`. A single workbook will not run unless you place the pack's `data` folder next to it.

[Download MCP-TC43-CreditCurve.xlsx](./MCP-TC43-CreditCurve.xlsx)

## **Object chain**

1. `=McpLiveMarketDataStore("data/market_data/MCP_MARKET_DATA_20260827.json")`  
2. `=mdlsGetCreditCurve(Store,"CNY_CREDIT_CFETS")` → `McpCreditCurve@n`  
3. `=CreditCurveHazardRate(curve, date)` / `CreditCurveDefaultProbability`

RawMD: `=McpRawMarketManager("data/market_data")` → `rawmdGetCreditCurve`  
JsonReader: `=mdjsonGetCreditCurve`

Valuation date: 2026-08-27

## **Key functions**

| Function | Description |
|----------|-------------|
| [mdlsGetCreditCurve](/latest/api/rawmarketdata.html) | LiveStore CreditCurve |
| [rawmdGetCreditCurve](/latest/api/rawmarketdata.html) | RawMD object |
| CreditCurveHazardRate | Hazard rate |
| CreditCurveDefaultProbability | Default probability |

## **Python example**

See `example/market_data/creditcurve_demo.py`.

## **Troubleshooting**

- `#NAME?`: register `mcp_market_data_live` / `mcp_raw_market_data` and Reload PyXLL
- Directory must contain `MCP_MARKET_DATA_20260827.json`
- Do not use removed skip-object UDFs
- C++ `buildCreditCurve` may fail intermittently: F9 again; `mdlsGetCreditCurve` retries 3 times, `rawmdGetCreditCurve` falls back to the Python builder
