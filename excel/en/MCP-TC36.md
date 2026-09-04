# **Implied YieldCurve Case Study**

> Visit the Mathema Option Pricing System for foreign exchange options and structured product valuation!
[![Visit the Mathema Option Pricing System](../pic/mathema.png)](https://fxo.mathema.com.cn)

FX-implied USD: JSON `USDDEPO_IMPLIED` (`CNHDEPO` + `USDCNH_FXFP_BGN`, `IsCCY2=false`) vs Direct `McpYieldCurve` VP.

## **Overview**

FX-implied USD yield: load JSON `USDDEPO_IMPLIED` (`CNHDEPO` + `USDCNH_FXFP_BGN`, `IsCCY2=false`) and compare with Direct `McpYieldCurve(FXFP, YC, IsCCY2, Calendar)` VP.

Data: `data/market_data/MCP_MARKET_DATA_20260626.json`, valuation date 2026-06-26. Key sheets: `Config` (shared Manager), `RawMD`, `Direct`, `Compare` (cross-sheet curve refs). After F9, `YieldCurveZeroRate` on both paths should align.

> **Ready to run**: Download the [TC31–TC46 example pack](/download/MCP-TC31-46-LiveStoreRawMD.zip) (all workbooks plus shared `data/`). Unzip and open the xlsx under `en`. A single workbook will not run unless you place the pack's `data` folder next to it.

[Download MCP-TC36-ImpliedYieldCurve.xlsx](./MCP-TC36-ImpliedYieldCurve.xlsx)

## **Object chain**

1. `=McpRawMarketManager("data/market_data")`  
2. `=rawmdGetYieldCurve(mgr,"USDDEPO_IMPLIED",val_date)`  
3. `=YieldCurveZeroRate(curve, date)`  
4. Direct: `=McpYieldCurve(FXFP, YC, IsCCY2, Calendar)` VP

MarketDataRoot: `data/market_data` (relative). Valuation date 2026-06-26.

## **Key functions**

| Function | Description |
|----------|-------------|
| [rawmdGetYieldCurve](/latest/api/rawmarketdata.html) | Implied / single-sided YC |
| [McpYieldCurve](/latest/api/yieldcurve.html) | Direct implied ctor |
| [YieldCurveZeroRate](/latest/api/yieldcurve.html) | Zero rate |

## **Python example**

See `example/market_data/implied_yc_demo.py`.

## **Troubleshooting**

- Snapshot must contain `CNHDEPO`, `USDCNH_FXFP_BGN`, `USDDEPO_IMPLIED`
- `#NAME?`: register `mcp_raw_market_data`
