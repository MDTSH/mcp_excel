# **Cross FXFP2 RawMD vs Direct Case Study**

> Visit the Mathema Option Pricing System for foreign exchange options and structured product valuation!
[![Visit the Mathema Option Pricing System](../pic/mathema.png)](https://fxo.mathema.com.cn)

Same pillars: JSON (RawMD / C++ Manager) vs Excel VP (Direct Cross from legs); plus `Fxfpc2GetCurve` vs rawmd mid-from-2.

## **Overview**

Same valuation date: build cross FX forward-points curve `CNHTHB_FXFP_CROSS_2` two ways — JSON RawMD (`rawmdGetFXForwardPointsCurve2` via C++ Manager) vs Excel Direct VP (`McpFXForwardPointsCurve2` from legs `USDTHB_FXFP_BGN_2` / `USDCNH_FXFP_BGN_2`). Then extract the mid curve with `Fxfpc2GetCurve` and compare to `rawmdGetFXForwardPointsCurve` MidFrom2.

Data: `data/market_data/MCP_MARKET_DATA_20260626.json`. Key sheets: `Config` (paths / date / Manager), `PillarData` (pillars for Direct VP), `Compare_YC2` / `Compare_FXFP2` / `Compare_Cross2` (RawMD vs Direct), `Curve_From2` (GetCurve vs MidFrom2). After F9, same-tenor diffs should be near zero.

> **Ready to run**: Download the [TC31–TC46 example pack](/download/MCP-TC31-46-LiveStoreRawMD.zip) (all workbooks plus shared `data/`). Unzip and open the xlsx under `en`. A single workbook will not run unless you place the pack's `data` folder next to it.

[Download MCP-TC35-CrossFXFP2RawMDvsDirect.xlsx](./MCP-TC35-CrossFXFP2RawMDvsDirect.xlsx)

## **Object chain**

1. `=McpRawMarketManager("data/market_data")`  
2. `=rawmdGetFXForwardPointsCurve2(mgr,"CNHTHB_FXFP_CROSS_2",val_date)`  
3. `=Fxfpc2FXForwardOutright(curve, date, "MID")`  
4. `=Fxfpc2GetCurve(curve2,"MID")` vs `rawmdGetFXForwardPointsCurve(...,"CNHTHB_FXFP_CROSS",...)`

Relative JSON: `data/market_data/MCP_MARKET_DATA_20260626.json`

curve_ids: `CNHTHB_FXFP_CROSS_2`, `USDTHB_FXFP_BGN_2`, `USDCNH_FXFP_BGN_2`, `CNHDEPO_2`

## **Key functions**

| Function | Description |
|----------|-------------|
| [rawmdGetFXForwardPointsCurve2](/latest/api/rawmarketdata.html) | Cross2 / FXFP2 object |
| [McpFXForwardPointsCurve2](/latest/api/fxforwardratecurve.html) | Direct VP (Leg1/Leg2) |
| [Fxfpc2GetCurve](/latest/api/fxforwardratecurve.html) | Curve2 → mid curve |

## **Python example**

See `example/market_data/cross_fxfp2_demo.py` — **LiveStore required**; Python RawMD cannot build Cross2 (no Tenors in JSON).

## **Troubleshooting**

- MarketDataRoot: `data/market_data` (relative to workbook)
- `#NAME?`: register `mcp_raw_market_data` and Reload PyXLL
