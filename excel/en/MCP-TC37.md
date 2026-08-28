# **Cross-Currency Basis Curve Case Study**

> Visit the Mathema Option Pricing System for foreign exchange options and structured product valuation!
[![Visit the Mathema Option Pricing System](../pic/mathema.png)](https://fxo.mathema.com.cn)

Standalone sample JSON (not the `MCP_MARKET_DATA` index): KV Direct (Path A2 / B) and `McpXccyBasisCurveFromJson`.

## **Overview**

Standalone cross-currency basis sample (not the `MCP_MARKET_DATA` index): KV Direct Path A2 (existing FXFP) and Path B (`BasisSpreads`), plus `McpXccyBasisCurveFromJson`.

Data: `data/XCCY_BASIS_CURVE_SAMPLE.json` (workbook-relative via `McpResolvePath`). Key sheets: `KV_Direct` (flat input curves + Path A2/B + DF/spread checks), `FromJson` (same curve_ids from JSON). After F9, read with `XccyBasisCurveDiscountFactor` / `XccyBasisCurveSpread`; hard checks use DF / SpotSpr_bp.

[Download MCP-TC37-XccyBasis.xlsx](./MCP-TC37-XccyBasis.xlsx)

## **Object chain**

1. Build input `McpYieldCurve` / `McpFXForwardPointsCurve` via VP  
2. `=McpXccyBasisCurve(...)` Path A2 (FXFP) or Path B (BasisSpreads)  
3. `=McpXccyBasisCurveFromJson(McpResolvePath("data/XCCY_BASIS_CURVE_SAMPLE.json"), ...)`  
4. `=XccyBasisCurveDiscountFactor` / `XccyBasisCurveSpread`

Sample: `data/XCCY_BASIS_CURVE_SAMPLE.json` (relative to workbook)

## **Key functions**

| Function | Description |
|----------|-------------|
| McpXccyBasisCurve | KV VP ctor |
| McpXccyBasisCurveFromJson | Load standalone JSON |
| XccyBasisCurveDiscountFactor | Read DF |

## **Python example**

See `excel/test_xccy_basis_curve.py`. This case does not use `excel/data/market_data/` snapshots.

## **Troubleshooting**

- Use workbook-relative path + `McpResolvePath` (no drive-letter absolutes)
- FXFP requires Calendar
