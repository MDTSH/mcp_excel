# **TRC LocalVol 案例（TrippleRangesCall）**


> 访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！
[![访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！](../pic/mathema.png)](https://fxo.mathema.com.cn)

TRC 即 **TrippleRangesCall**（三重区间看涨）。从裁剪快照用 `mdlsGetLocalVol` 取 `EURUSD_LOCALVOL`，再交给已有 `McpStructuredDerivativeProduct` 做 Dupire 定价。

**功能描述：** LiveStore 表取 LocalVol / 贴现曲线；TRC定价表填 SDP 要素（YAML 相对路径）并输出 XssPrice / XssPV。MC 默认 2000 路径，F9 后约数十秒。

[下载 MCP-TC41-TRCLocalVol.xlsx](./MCP-TC41-TRCLocalVol.xlsx)

## **对象链**

1. `=McpLiveMarketDataStore("data/market_data/MCP_MARKET_DATA_P2_LOCALVOL_20260810.json")`  
2. `=mdlsGetLocalVol(Store,"EURUSD_LOCALVOL")` → `McpLocalVol@n`  
3. `=mdlsGetYieldCurve(Store,"CNYDEPO")`  
4. `=McpStructuredDerivativeProduct(..., LocalVol=对象, ConfigPath=YAML)`  
5. `=XssPrice` / `XssPV`

YAML：`data/structured_products/tripplerangescall.yaml`（相对工作簿）

备选：`mdlsGetCurveBySection(Store,"FXVolSurface","USDCNY_RVOL_BGN")` → `McpLocalVol` 短构造（v1 曲面，不要用 FXVolSurface2）。

## **主要函数**

| 函数 | 说明 |
|------|------|
| [mdlsGetLocalVol](/zh/latest/api/rawmarketdata.html) | 取 LocalVol 对象 |
| [LocalVolGetVolatility](/zh/latest/api/localvol.html) | 读局部波动率 |
| [McpStructuredDerivativeProduct](/zh/latest/api/xss.html) | SDP（LocalVol） |
| [XssPrice](/zh/latest/api/xss.html) | 价格 |

## **Python 示例**

完整示例：`example/market_data/localvol_demo.py`（读 LocalVol；SDP 定价以本 Excel 为准）

## **排错**

- `#NAME?`：注册 `mcp_market_data_live`、`xscript` 并 Reload PyXLL
- LocalVol 需要 FXVolSurface **v1** 或 JSON `LocalVol` 节
- ConfigPath 须相对工作簿，且 PackageName=`TrippleRangesCall`
