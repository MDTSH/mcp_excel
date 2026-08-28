# **BondCurve Bootstrap 案例**


> 访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！
[![访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！](../pic/mathema.png)](https://fxo.mathema.com.cn)

嵌入样本券 Bootstrap（CGB / CDB）+ 可选 RawMD `CNY_BOND_TREASURY`（times_and_rates）。

## **功能描述**

演示国债 / 国开债 BondCurve 嵌入样本券 Bootstrap：`McpBillCurveData` + `McpFixedRateBondCurveData` → `McpCalibrationSet` → `McpBondCurve`，再读 ZeroRate / DF / ParRate。可选 RawMD 路径取 `CNY_BOND_TREASURY`（times_and_rates，不是券面 bootstrap）。

主要 Sheet：`CGB`（CGB_v9，估值日 2026-04-13）、`CDB`（CDB_v3 + 1Y fill）、`RawMD`（JSON `MCP_MARKET_DATA_20260626.json`，估值日 2026-06-26）。F9 后各 Sheet 应给出曲线对象并填出读数。

[下载 MCP-TC38-BondCurveBootstrap.xlsx](./MCP-TC38-BondCurveBootstrap.xlsx)

## **对象链**

**嵌入券（CGB / CDB）：**

1. `=McpBillCurveData` + `=McpFixedRateBondCurveData`  
2. `=McpCalibrationSet` → `=McpBondCurve`  
3. `=BondCurveZeroRate` / `BondCurveDiscountFactor` / `BondCurveParRate`

**可选 RawMD：**

`McpRawMarketManager("data/market_data")` → `rawmdGetBondCurve(mgr,"CNY_BOND_TREASURY",估值日)` → `BondCurveZeroRate`

估值日：嵌入券 2026-04-13；RawMD JSON 2026-06-26

## **主要函数**

| 函数 | 说明 |
|------|------|
| McpBondCurve | Bootstrap 构造 |
| [rawmdGetBondCurve](/zh/latest/api/rawmarketdata.html) | JSON BondCurve |
| [BondCurveZeroRate](/zh/latest/api/yieldcurve.html) | 读零息 |

## **Python 示例**

```python
from excel.raw_market_data.raw_market_data_loader import RawMarketDataManager
mgr = RawMarketDataManager(root="excel/data/market_data")
bc = mgr.get_bond_curve("CNY_BOND_TREASURY", "2026-06-26")
```

CGB/CDB 嵌入路径以工作簿为准；RawMD 为 times_and_rates，不是券面 bootstrap。

## **排错**

- Bill `BUses` 须为 `Y`（勿写数字 1）
- InterpolationMethod 下拉：LINEARINTERPOLATION / CUBICSPLINES
- RawMD 根目录相对工作簿：`data/market_data`
