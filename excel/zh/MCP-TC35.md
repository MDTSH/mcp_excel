# **Cross FXFP2 RawMD vs Direct 案例**


> 访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！
[![访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！](../pic/mathema.png)](https://fxo.mathema.com.cn)

同一 pillar：JSON 路径（RawMD / C++ Manager）vs Excel VP（Direct Leg Cross）；并对比 `Fxfpc2GetCurve` 与 rawmd 单边 MidFrom2。

## **功能描述**

同一估值日对比交叉外汇远期点曲线 `CNHTHB_FXFP_CROSS_2` 的两条路径：JSON RawMD（C++ `rawmdGetFXForwardPointsCurve2`）与 Excel Direct VP（`McpFXForwardPointsCurve2`，双腿 `USDTHB_FXFP_BGN_2` / `USDCNH_FXFP_BGN_2`）。再用 `Fxfpc2GetCurve` 抽出单边 Mid，对照 `rawmdGetFXForwardPointsCurve` 的 MidFrom2。

数据：`data/market_data/MCP_MARKET_DATA_20260626.json`。主要 Sheet：`Config`（路径 / 估值日 / Manager）、`PillarData`（Direct 引用的 pillar）、`Compare_YC2` / `Compare_FXFP2` / `Compare_Cross2`（RawMD vs Direct）、`Curve_From2`（GetCurve vs MidFrom2）。F9 后同 tenor 的 Diff 应接近 0。

[下载 MCP-TC35-CrossFXFP2RawMDvsDirect.xlsx](./MCP-TC35-CrossFXFP2RawMDvsDirect.xlsx)

## **对象链**

1. `=McpRawMarketManager("data/market_data")`  
2. `=rawmdGetFXForwardPointsCurve2(mgr,"CNHTHB_FXFP_CROSS_2",估值日)` → `McpFXForwardPointsCurve2@n`  
3. `=Fxfpc2FXForwardOutright(曲线, 日期, "MID")`  
4. `=Fxfpc2GetCurve(curve2,"MID")` vs `=rawmdGetFXForwardPointsCurve(mgr,"CNHTHB_FXFP_CROSS",估值日)`

JSON：`data/market_data/MCP_MARKET_DATA_20260626.json`（相对工作簿）

curve_id：`CNHTHB_FXFP_CROSS_2`、`USDTHB_FXFP_BGN_2`、`USDCNH_FXFP_BGN_2`、`CNHDEPO_2`

## **主要函数**

| 函数 | 说明 |
|------|------|
| [rawmdGetFXForwardPointsCurve2](/zh/latest/api/rawmarketdata.html) | 取 Cross2 / 双边 FXFP2 |
| [McpFXForwardPointsCurve2](/zh/latest/api/fxforwardratecurve.html) | Direct VP（Leg1/Leg2） |
| [Fxfpc2FXSpotRate](/zh/latest/api/fxforwardratecurve.html) | Spot MID/BID/ASK |
| [Fxfpc2GetCurve](/zh/latest/api/fxforwardratecurve.html) | Curve2 → 单边 Mid |

## **Python 示例**

```python
import mcp.mcp as mcp
store = mcp.MLiveMarketDataStore()
store.loadSnapshot("excel/data/market_data/MCP_MARKET_DATA_20260626.json")
fx = store.getFXForwardPointsCurve2("CNHTHB_FXFP_CROSS_2")
print(fx.FXSpotRate("MID"))
```

完整示例：`example/market_data/cross_fxfp2_demo.py`（**须 LiveStore**；Python RawMD 无法构建无 Tenors 的 Cross2）

## **排错**

- MarketDataRoot 设为 `data/market_data`（相对工作簿）
- Cross2 JSON 无 Tenors；Excel `rawmdGet*` 走 C++ Manager
- `#NAME?`：注册 `mcp_raw_market_data` 并 Reload PyXLL
