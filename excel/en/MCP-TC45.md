# **ForwardCurve (non-FX) Case**


> Visit the Mathema Option Pricing System for FX options and structured-product valuation!
[![Visit the Mathema Option Pricing System](../pic/mathema.png)](https://fxo.mathema.com.cn)

Load a **non-FX** forward curve (`ExpiryDates` + `UnderlyingRates`) from standard JSON, then read with `ForwardCurveForwardRate`.

**What it does:** LiveStore / RawMD get `EQ_FORWARD`; the first pillar (2026-09-28) is about 100.5. This is not `FXForwardPointsCurve2` (P0/P1).

[Download MCP-TC45-ForwardCurve.xlsx](./MCP-TC45-ForwardCurve.xlsx)

## **Object chain**

1. `=McpLiveMarketDataStore("data/market_data/MCP_MARKET_DATA_20260827.json")`  
2. `=mdlsGetForwardCurve(Store,"EQ_FORWARD")` → `McpForwardCurve@n`  
3. `=ForwardCurveForwardRate(curve, date)`

RawMD: `=rawmdGetForwardCurve(mgr,"EQ_FORWARD",val_date)`

## **Key functions**

| Function | Description |
|----------|-------------|
| [mdlsGetForwardCurve](/latest/api/rawmarketdata.html) | LiveStore ForwardCurve |
| [rawmdGetForwardCurve](/latest/api/rawmarketdata.html) | RawMD object |
| ForwardCurveForwardRate | Forward price |

## **Python example**

See `example/market_data/forwardcurve_demo.py`.

## **Troubleshooting**

- `#NAME?`: register modules and Reload PyXLL
- Do not mix with FX forward-points UDFs
