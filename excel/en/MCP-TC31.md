# **LiveStore Market Data Case Study**

> Visit the Mathema Option Pricing System for foreign exchange options and structured product valuation!
[![Visit the Mathema Option Pricing System](../pic/mathema.png)](https://fxo.mathema.com.cn)

Load standard `MCP_MARKET_DATA` JSON into LiveStore, get curve objects via `mdlsGet*`, read rates with `YieldCurve2ZeroRate`; demonstrates patch and Impact.

> **Ready to run**: Download the [TC31–TC46 example pack](/download/MCP-TC31-46-LiveStoreRawMD.zip) (all workbooks plus shared `data/`). Unzip and open the xlsx under `en`. A single workbook will not run unless you place the pack's `data` folder next to it.

[Download MCP-TC31-LiveStoreMarketData.xlsx](./MCP-TC31-LiveStoreMarketData.xlsx)

## **Object chain**

1. `=McpLiveMarketDataStore(Config!B2)`  
2. `=mdlsGetYieldCurve2(Store,"CNHDEPO_2")` → `McpYieldCurve2@n`  
3. `=YieldCurve2ZeroRate(curve, date, "MID")`  
4. `=mdlsApplyUpdateFile(Store, patch path)` — must be referenced before post-patch reads  
5. `=mdlsLastUpdateImpact(Store)`

Relative paths: `data/market_data/MCP_MARKET_DATA_20260810.json`, `MCP_PATCH_CNHDEPO.json`

## **Key functions**

| Function | Description |
|----------|-------------|
| [McpLiveMarketDataStore](/latest/api/rawmarketdata.html) | Load snapshot |
| [mdlsGetYieldCurve2](/latest/api/rawmarketdata.html) | Get YieldCurve2 object |
| [mdlsApplyUpdateFile](/latest/api/rawmarketdata.html) | Apply patch |
| [YieldCurve2ZeroRate](/latest/api/yieldcurve.html) | Read zero rate |

## **Python example**

See `example/market_data/livestore_demo.py` and `patch_dod_demo.py`.

## **Troubleshooting**

- `#NAME?`: register `mcp_market_data_live`, `mcp_lifecycle` (last) in `pyxll.cfg`
- Patch not applied: ensure `mdlsApplyUpdateFile` is referenced by downstream cells
