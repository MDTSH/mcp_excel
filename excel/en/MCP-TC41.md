# **TRC LocalVol Case (TrippleRangesCall)**


> Visit the Mathema Option Pricing System for FX options and structured-product valuation!
[![Visit the Mathema Option Pricing System](../pic/mathema.png)](https://fxo.mathema.com.cn)

TRC means **TrippleRangesCall**. Load `EURUSD_LOCALVOL` with `mdlsGetLocalVol`, then price via `McpStructuredDerivativeProduct` (Dupire).

**What it does:** LiveStore returns LocalVol and the discount curve; TRC定价 fills SDP fields (YAML relative path) and shows XssPrice / XssPV. Default 2000 MC paths — F9 may take tens of seconds.

> **Ready to run**: Download the [TC31–TC46 example pack](/download/MCP-TC31-46-LiveStoreRawMD.zip) (all workbooks plus shared `data/`). Unzip and open the xlsx under `en`. A single workbook will not run unless you place the pack's `data` folder next to it.

[Download MCP-TC41-TRCLocalVol.xlsx](./MCP-TC41-TRCLocalVol.xlsx)

## **Object chain**

1. `=McpLiveMarketDataStore("data/market_data/MCP_MARKET_DATA_P2_LOCALVOL_20260810.json")`  
2. `=mdlsGetLocalVol(Store,"EURUSD_LOCALVOL")`  
3. `=mdlsGetYieldCurve(Store,"CNYDEPO")`  
4. `=McpStructuredDerivativeProduct(..., LocalVol=object)`  
5. `=XssPrice` / `XssPV`

YAML: `data/structured_products/tripplerangescall.yaml` (relative to the workbook)

Fallback: `mdlsGetCurveBySection(Store,"FXVolSurface","USDCNY_RVOL_BGN")` → short `McpLocalVol` (v1 surface, not FXVolSurface2).

## **Key functions**

| Function | Description |
|----------|-------------|
| [mdlsGetLocalVol](/latest/api/rawmarketdata.html) | LocalVol object |
| LocalVolGetVolatility | Local vol read |
| McpStructuredDerivativeProduct | SDP |
| XssPrice | Price |

## **Python example**

See `example/market_data/localvol_demo.py` (reads LocalVol; SDP pricing is this workbook).

## **Troubleshooting**

- `#NAME?`: register `mcp_market_data_live` and `xscript`, then Reload PyXLL
- LocalVol needs FXVolSurface **v1** or a JSON `LocalVol` section
- ConfigPath must be relative; PackageName=`TrippleRangesCall`
