# **RawMD vs Direct Construction Case Study**

> Visit the Mathema Option Pricing System!
[![Visit the Mathema Option Pricing System](../pic/mathema.png)](https://fxo.mathema.com.cn)

Same pillar data: JSON (RawMD) vs Excel VP construction (Direct).

> **Ready to run**: Download the [TC31–TC46 example pack](/download/MCP-TC31-46-LiveStoreRawMD.zip) (all workbooks plus shared `data/`). Unzip and open the xlsx under `en`. A single workbook will not run unless you place the pack's `data` folder next to it.

[Download MCP-TC33-RawMDvsDirect.xlsx](./MCP-TC33-RawMDvsDirect.xlsx)

## **Comparison (P0)**

- **Compare_YC2**: `CNHDEPO_2`  
- **Compare_FXFP2**: `USDCNH_FXFP_BGN_2`  

Diff columns should be near 0 bp.

## **Key functions**

| RawMD | Direct | Read |
|-------|--------|------|
| rawmdGetYieldCurve2 | McpYieldCurve2 | YieldCurve2ZeroRate |
| rawmdGetFXForwardPointsCurve2 | McpFXForwardPointsCurve2 | Fxfpc2FXSpotRate |

MarketDataRoot: `data/market_data` (relative to workbook).
