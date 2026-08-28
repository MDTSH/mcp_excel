# **BondSpreadCurve Case**


> Visit the Mathema Option Pricing System for FX options and structured-product valuation!
[![Visit the Mathema Option Pricing System](../pic/mathema.png)](https://fxo.mathema.com.cn)

Load a bond-spread curve from a JSON `two_curves` entry, read `zeroSpread`, then shock the benchmark with a `YieldCurve`.

**What it does:** `CNY_BOND_POLICY_SPREAD` = treasury `CNY_BOND_TREASURY` vs policy `CNY_BOND_POLICY` (small times_and_rates samples). `rawmdBondSpreadSetBenchmark` requires an `MYieldCurve` (`CNYDEPO_BUMP`), not a BondCurve. Use C++ LiveStore / Manager; Python fromJson cannot build two_curves.

[Download MCP-TC44-BondSpreadCurve.xlsx](./MCP-TC44-BondSpreadCurve.xlsx)

## **Object chain**

1. `=McpLiveMarketDataStore("data/market_data/MCP_MARKET_DATA_20260827.json")`  
2. `=mdlsGetBondSpreadCurve(Store,"CNY_BOND_POLICY_SPREAD")`  
3. `=BondSpreadCurveZeroSpread(curve, date)`  
4. `=rawmdBondSpreadSetBenchmark(spread, mdlsGetYieldCurve(Store,"CNYDEPO_BUMP"))`

RawMD: `rawmdGetBondSpreadCurve` + `rawmdGetYieldCurve`

After the benchmark swap, ZeroRate stays the same (adjusted curve unchanged); zeroSpread changes.

## **Key functions**

| Function | Description |
|----------|-------------|
| [mdlsGetBondSpreadCurve](/latest/api/rawmarketdata.html) | LiveStore spread curve |
| [rawmdGetBondSpreadCurve](/latest/api/rawmarketdata.html) | RawMD object |
| rawmdBondSpreadSetBenchmark | Replace benchmark (MYieldCurve) |
| BondSpreadCurveZeroSpread | Zero spread |

## **Python example**

See `example/market_data/bondspread_demo.py`.

## **Troubleshooting**

- `#NAME?`: register `mcp_market_data_live` / `mcp_raw_market_data` and Reload PyXLL
- `setBenchmarkCurve` type error: argument 2 must be a YieldCurve
- Python RawMD returns empty: use C++ Manager / LiveStore
