# **VolSurface（非 FX）案例**


> 访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！
[![访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！](../pic/mathema.png)](https://fxo.mathema.com.cn)

从裁剪后的非 FX 波动率曲面取对象，再用已有 `VolSurfaceGetVolatility` 读数。

**功能描述：** `EQ_VOL_SAMPLE` 为 2 个到期 × 5 个行权价的小网格（`UsingImpVols`，依赖 `CNYDEPO`）。`ExpiryDates` 须与 `Strikes` 等长（逐点展开）。不是 `FXVolSurface2`（P0/TC40）。

[下载 MCP-TC46-VolSurface.xlsx](./MCP-TC46-VolSurface.xlsx)

## **对象链**

1. `=McpLiveMarketDataStore("data/market_data/MCP_MARKET_DATA_20260827.json")`  
2. `=mdlsGetVolSurface(Store,"EQ_VOL_SAMPLE")` → `McpVolSurface@n`  
3. `=VolSurfaceGetVolatility(曲面, 100, 到期日, 0)`

RawMD：`=rawmdGetVolSurface(mgr,"EQ_VOL_SAMPLE",估值日)`

ATM（100, 2026-09-28）隐含波动率约为 0.20。

## **主要函数**

| 函数 | 说明 |
|------|------|
| [mdlsGetVolSurface](/zh/latest/api/rawmarketdata.html) | LiveStore 取 VolSurface |
| [rawmdGetVolSurface](/zh/latest/api/rawmarketdata.html) | RawMD 取对象 |
| VolSurfaceGetVolatility | 读波动率 |

## **Python 示例**

完整示例：`example/market_data/volsurface_demo.py`

## **排错**

- `#NAME?`：注册模块并 Reload PyXLL
- 曲面构建失败：检查 `ExpiryDates`/`Strikes`/`Premiums`/`ImpVols` 长度一致，且含 `risk_free_rate_curve`
