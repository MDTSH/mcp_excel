# **RawMD 目录管理器案例**


> 访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！
[![访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！](../pic/mathema.png)](https://fxo.mathema.com.cn)

目录模式：指向含 `MCP_MARKET_DATA_YYYYMMDD.json` 的文件夹，按估值日取曲线对象。

> **打开即可用**：请下载 [TC31–TC46 完整案例包](/download/MCP-TC31-46-LiveStoreRawMD.zip)（含全部工作簿和共用的 `data/`）。解压后打开 `zh` 目录里的 xlsx。只下单个工作簿时，必须把包里的 `data` 文件夹放到与 xlsx **同一目录**。

[下载 MCP-TC32-RawMarketManager.xlsx](./MCP-TC32-RawMarketManager.xlsx)

## **对象链**

`McpRawMarketManager("data/market_data")` → `rawmdGetYieldCurve2(mgr, id, 估值日)` → `YieldCurve2ZeroRate`

## **主要函数**

| 函数 | 说明 |
|------|------|
| [McpRawMarketManager](/zh/latest/api/rawmarketdata.html#excel-mcprawmarketmanager-market-data-root) | 目录 Manager |
| [rawmdGetYieldCurve2](/zh/latest/api/rawmarketdata.html#excel-rawmdgetyieldcurve2-manager-curve-id-valuation-date) | 按日取 YC2 |
| [rawmdAvailableDates](/zh/latest/api/rawmarketdata.html#excel-rawmdavailabledates-manager) | 可用估值日 |
| [rawmdLatestValuationDate](/zh/latest/api/rawmarketdata.html#excel-rawmdlatestvaluationdate-manager) | 最新估值日 |

## **Python 示例**

```python
from excel.raw_market_data.raw_market_data_loader import RawMarketDataManager
mgr = RawMarketDataManager(root="excel/data/market_data")
dates = mgr.get_available_dates()
yc2 = mgr.get_yield_curve2("CNHDEPO_2", dates[-1])
print(yc2.getInstance().ZeroRate("2026/08/10", "MID"))
```

见 `example/market_data/rawmd_demo.py`

## **排错**

- 目录须含 `MCP_MARKET_DATA_20260810.json` 格式主索引
- `#NAME?`：注册 `mcp_raw_market_data` 模块
