# **ForwardCurve（非 FX）案例**


> 访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！
[![访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！](../pic/mathema.png)](https://fxo.mathema.com.cn)

从标准 JSON 取**非外汇**远期曲线（股指/商品式 `ExpiryDates` + `UnderlyingRates`），再用 `ForwardCurveForwardRate` 读数。

**功能描述：** LiveStore / RawMD 对 `EQ_FORWARD` 取对象；第一根 pillar（2026-09-28）远期约为 100.5。这不是 `FXForwardPointsCurve2`（P0/P1）。

[下载 MCP-TC45-ForwardCurve.xlsx](./MCP-TC45-ForwardCurve.xlsx)

## **对象链**

1. `=McpLiveMarketDataStore("data/market_data/MCP_MARKET_DATA_20260827.json")`  
2. `=mdlsGetForwardCurve(Store,"EQ_FORWARD")` → `McpForwardCurve@n`  
3. `=ForwardCurveForwardRate(曲线, 日期)`

RawMD：`=rawmdGetForwardCurve(mgr,"EQ_FORWARD",估值日)`

## **主要函数**

| 函数 | 说明 |
|------|------|
| [mdlsGetForwardCurve](/zh/latest/api/rawmarketdata.html) | LiveStore 取 ForwardCurve |
| [rawmdGetForwardCurve](/zh/latest/api/rawmarketdata.html) | RawMD 取对象 |
| ForwardCurveForwardRate | 读远期价格 |

## **Python 示例**

完整示例：`example/market_data/forwardcurve_demo.py`

## **排错**

- `#NAME?`：注册模块并 Reload PyXLL
- 不要与 FX 远期点曲线 UDF 混用
