# **VolSurface (non-FX) Case**


> Visit the Mathema Option Pricing System for FX options and structured-product valuation!
[![Visit the Mathema Option Pricing System](../pic/mathema.png)](https://fxo.mathema.com.cn)

Load a trimmed non-FX volatility surface, then read with existing `VolSurfaceGetVolatility`.

**What it does:** `EQ_VOL_SAMPLE` is a 2-expiry × 5-strike grid (`UsingImpVols`, depends on `CNYDEPO`). `ExpiryDates` must be the same length as `Strikes` (one row per point). This is not `FXVolSurface2` (P0/TC40).

[Download MCP-TC46-VolSurface.xlsx](./MCP-TC46-VolSurface.xlsx)

## **Object chain**

1. `=McpLiveMarketDataStore("data/market_data/MCP_MARKET_DATA_20260827.json")`  
2. `=mdlsGetVolSurface(Store,"EQ_VOL_SAMPLE")` → `McpVolSurface@n`  
3. `=VolSurfaceGetVolatility(surface, 100, expiry, 0)`

RawMD: `=rawmdGetVolSurface(mgr,"EQ_VOL_SAMPLE",val_date)`

ATM (100, 2026-09-28) implied vol is about 0.20.

## **Key functions**

| Function | Description |
|----------|-------------|
| [mdlsGetVolSurface](/latest/api/rawmarketdata.html) | LiveStore VolSurface |
| [rawmdGetVolSurface](/latest/api/rawmarketdata.html) | RawMD object |
| VolSurfaceGetVolatility | Volatility |

## **Python example**

See `example/market_data/volsurface_demo.py`.

## **Troubleshooting**

- `#NAME?`: register modules and Reload PyXLL
- Build failed: `ExpiryDates` / `Strikes` / `Premiums` / `ImpVols` must match in length; include `risk_free_rate_curve`
