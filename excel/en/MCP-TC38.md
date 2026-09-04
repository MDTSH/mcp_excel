# **BondCurve Bootstrap Case Study**

> Visit the Mathema Option Pricing System for foreign exchange options and structured product valuation!
[![Visit the Mathema Option Pricing System](../pic/mathema.png)](https://fxo.mathema.com.cn)

Embedded-bond bootstrap (CGB / CDB) plus optional RawMD `CNY_BOND_TREASURY` (times_and_rates).

## **Overview**

Embedded-bond BondCurve bootstrap for CGB / CDB: `McpBillCurveData` + `McpFixedRateBondCurveData` → `McpCalibrationSet` → `McpBondCurve`, then ZeroRate / DF / ParRate. Optional RawMD path loads `CNY_BOND_TREASURY` (times_and_rates, not bond-by-bond bootstrap).

Key sheets: `CGB` (CGB_v9, valuation 2026-04-13), `CDB` (CDB_v3 + 1Y fill), `RawMD` (`MCP_MARKET_DATA_20260626.json`, valuation 2026-06-26). After F9 each sheet should show a curve handle and populated reads.

> **Ready to run**: Download the [TC31–TC46 example pack](/download/MCP-TC31-46-LiveStoreRawMD.zip) (all workbooks plus shared `data/`). Unzip and open the xlsx under `en`. A single workbook will not run unless you place the pack's `data` folder next to it.

[Download MCP-TC38-BondCurveBootstrap.xlsx](./MCP-TC38-BondCurveBootstrap.xlsx)

## **Object chain**

**Embedded (CGB / CDB):**

`McpBillCurveData` + `McpFixedRateBondCurveData` → `McpCalibrationSet` → `McpBondCurve` → `BondCurveZeroRate`

**Optional RawMD:**

`McpRawMarketManager("data/market_data")` → `rawmdGetBondCurve(...,"CNY_BOND_TREASURY",...)` → `BondCurveZeroRate`

Dates: embedded 2026-04-13; RawMD JSON 2026-06-26.

## **Key functions**

| Function | Description |
|----------|-------------|
| McpBondCurve | Bootstrap ctor |
| [rawmdGetBondCurve](/latest/api/rawmarketdata.html) | JSON BondCurve |
| BondCurveZeroRate | Read zero |

## **Python example**

```python
mgr.get_bond_curve("CNY_BOND_TREASURY", "2026-06-26")
```

RawMD is times_and_rates, not bond-by-bond bootstrap.

## **Troubleshooting**

- Bill `BUses` must be `Y` (not numeric 1)
- MarketDataRoot: `data/market_data` (relative)
