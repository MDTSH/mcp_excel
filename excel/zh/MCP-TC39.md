# **FR007 SwapCurve RawMD 案例**


> 访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！
[![访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！](../pic/mathema.png)](https://fxo.mathema.com.cn)

从标准 JSON 按估值日取 FR007 掉期曲线对象，再用已有 `SwapCurveZeroRate` 读数。

## **功能描述**

演示从标准 JSON 按估值日取出 FR007 掉期曲线：`McpRawMarketManager` → `rawmdGetSwapCurve("CNY_SWAP_FR007_BGN")` → `SwapCurveZeroRate` / `SwapCurveDiscountFactor`。

数据：`data/market_data/MCP_MARKET_DATA_20260626.json`，估值日 2026-06-26。主要 Sheet：`Config`（路径 / 估值日 / Manager / curve_id）、`RawMD`（对象 + 各 tenor 零息与 DF）。F9 后曲线单元格应为 `McpSwapCurve@n`，各 tenor 有数。

> **打开即可用**：请下载 [TC31–TC46 完整案例包](/download/MCP-TC31-46-LiveStoreRawMD.zip)（含全部工作簿和共用的 `data/`）。解压后打开 `zh` 目录里的 xlsx。只下单个工作簿时，必须把包里的 `data` 文件夹放到与 xlsx **同一目录**。

[下载 MCP-TC39-FR007SwapCurveRawMD.xlsx](./MCP-TC39-FR007SwapCurveRawMD.xlsx)

## **对象链**

1. `=McpRawMarketManager("data/market_data")`  
2. `=rawmdGetSwapCurve(mgr,"CNY_SWAP_FR007_BGN",估值日)` → `McpSwapCurve@n`  
3. `=SwapCurveZeroRate(曲线, 日期)` / `SwapCurveDiscountFactor`

MarketDataRoot：`data/market_data`（相对工作簿），估值日 2026-06-26

## **主要函数**

| 函数 | 说明 |
|------|------|
| [McpRawMarketManager](/zh/latest/api/rawmarketdata.html) | 目录 Manager |
| [rawmdGetSwapCurve](/zh/latest/api/rawmarketdata.html) | 取 SwapCurve 对象 |
| [SwapCurveZeroRate](/zh/latest/api/yieldcurve.html) | 读零息 |

## **Python 示例**

```python
import mcp.mcp as mcp
mgr = mcp.MRawMarketManager("excel/data/market_data")
sc = mgr.getSwapCurve("CNY_SWAP_FR007_BGN", "2026-06-26")
print(sc.ZeroRate("2026/09/28"))
```

完整示例：`example/market_data/fr007_rawmd_demo.py`

## **排错**

- 目录须含 `MCP_MARKET_DATA_20260626.json`
- `#NAME?`：注册 `mcp_raw_market_data` 并 Reload PyXLL
- 勿使用已移除的 skip-object UDF
