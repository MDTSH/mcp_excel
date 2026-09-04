# **Implied YieldCurve 案例**


> 访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！
[![访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！](../pic/mathema.png)](https://fxo.mathema.com.cn)

FX 隐含利率：JSON 条目 `USDDEPO_IMPLIED`（`CNHDEPO` + `USDCNH_FXFP_BGN`，`IsCCY2=false`）对照 Direct `McpYieldCurve` VP 构造。

## **功能描述**

演示 FX 隐含利率：从 JSON 取 `USDDEPO_IMPLIED`（由 `CNHDEPO` + `USDCNH_FXFP_BGN`、`IsCCY2=false` 隐含 USD），对照 Direct `McpYieldCurve(FXFP, YC, IsCCY2, Calendar)` VP。

数据：`data/market_data/MCP_MARKET_DATA_20260626.json`，估值日 2026-06-26。主要 Sheet：`Config`（Manager 统一入口）、`RawMD`、`Direct`、`Compare`（跨表引用两条曲线）。F9 后两条路径的 `YieldCurveZeroRate` 应对齐。

> **打开即可用**：请下载 [TC31–TC46 完整案例包](/download/MCP-TC31-46-LiveStoreRawMD.zip)（含全部工作簿和共用的 `data/`）。解压后打开 `zh` 目录里的 xlsx。只下单个工作簿时，必须把包里的 `data` 文件夹放到与 xlsx **同一目录**。

[下载 MCP-TC36-ImpliedYieldCurve.xlsx](./MCP-TC36-ImpliedYieldCurve.xlsx)

## **对象链**

1. `=McpRawMarketManager("data/market_data")`  
2. `=rawmdGetYieldCurve(mgr,"USDDEPO_IMPLIED",估值日)` → `McpYieldCurve@n`  
3. `=YieldCurveZeroRate(曲线, 日期)`  
4. Direct：`=McpYieldCurve(FXForwardPointsCurve, YieldCurve, IsCCY2, Calendar)` VP

MarketDataRoot：`data/market_data`（相对工作簿），估值日 2026-06-26

## **主要函数**

| 函数 | 说明 |
|------|------|
| [rawmdGetYieldCurve](/zh/latest/api/rawmarketdata.html) | JSON implied / 单边 YC |
| [rawmdGetFXForwardPointsCurve](/zh/latest/api/rawmarketdata.html) | 锚定 FXFP |
| [McpYieldCurve](/zh/latest/api/yieldcurve.html) | Direct implied 构造 |
| [YieldCurveZeroRate](/zh/latest/api/yieldcurve.html) | 读零息 |

## **Python 示例**

```python
store = mcp.MLiveMarketDataStore()
store.loadSnapshot(json_path)
print(store.getYieldCurve("USDDEPO_IMPLIED").ZeroRate("2026/12/28"))
```

完整示例：`example/market_data/implied_yc_demo.py`

## **排错**

- 需同时存在 `CNHDEPO`、`USDCNH_FXFP_BGN`、`USDDEPO_IMPLIED`
- `#NAME?`：注册 `mcp_raw_market_data`
