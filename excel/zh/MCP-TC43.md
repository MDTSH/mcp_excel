# **CreditCurve 案例**


> 访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！
[![访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！](../pic/mathema.png)](https://fxo.mathema.com.cn)

从标准 JSON 取信用曲线对象，再用已有 `CreditCurveHazardRate` / `CreditCurveDefaultProbability` 读数。

**功能描述：** LiveStore / RawMD / JsonReader 三表对同一 `CNY_CREDIT_CFETS`（Spreads 单位 BP，依赖 `CNYDEPO`）取对象并读 1Y 风险率与违约概率。走 C++ Manager / Store。

[下载 MCP-TC43-CreditCurve.xlsx](./MCP-TC43-CreditCurve.xlsx)

## **对象链**

1. `=McpLiveMarketDataStore("data/market_data/MCP_MARKET_DATA_20260827.json")`  
2. `=mdlsGetCreditCurve(Store,"CNY_CREDIT_CFETS")` → `McpCreditCurve@n`  
3. `=CreditCurveHazardRate(曲线, 日期)` / `CreditCurveDefaultProbability`

RawMD：`=McpRawMarketManager("data/market_data")` → `rawmdGetCreditCurve(mgr,id,估值日)`  
JsonReader：`=mdjsonGetCreditCurve(reader,id)`

估值日：2026-08-27

## **主要函数**

| 函数 | 说明 |
|------|------|
| [mdlsGetCreditCurve](/zh/latest/api/rawmarketdata.html) | LiveStore 取 CreditCurve |
| [rawmdGetCreditCurve](/zh/latest/api/rawmarketdata.html) | RawMD 取对象 |
| CreditCurveHazardRate | 读风险率 |
| CreditCurveDefaultProbability | 读违约概率 |

## **Python 示例**

完整示例：`example/market_data/creditcurve_demo.py`

## **排错**

- `#NAME?`：注册 `mcp_market_data_live`、`mcp_raw_market_data` 并 Reload PyXLL
- 目录须含 `MCP_MARKET_DATA_20260827.json`
- 勿使用已移除的 skip-object UDF
- C++ `buildCreditCurve` 偶发校准失败：Reload / F9 再算；`mdlsGetCreditCurve` 会重试 3 次，`rawmdGetCreditCurve` 失败后走 Python 结构化构建
