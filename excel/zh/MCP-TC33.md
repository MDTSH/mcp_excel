# **RawMD vs 手工构造对比案例**


> 访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！
[![访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！](../pic/mathema.png)](https://fxo.mathema.com.cn)

同一 pillar 数据：JSON 路径（RawMD）vs Excel 内嵌 VP 构造（Direct），对比 `YieldCurve2ZeroRate` / `Fxfpc2FXSpotRate`。

> **打开即可用**：请下载 [TC31–TC46 完整案例包](/download/MCP-TC31-46-LiveStoreRawMD.zip)（含全部工作簿和共用的 `data/`）。解压后打开 `zh` 目录里的 xlsx。只下单个工作簿时，必须把包里的 `data` 文件夹放到与 xlsx **同一目录**。

[下载 MCP-TC33-RawMDvsDirect.xlsx](./MCP-TC33-RawMDvsDirect.xlsx)

## **对比内容（P0）**

- **Compare_YC2**：`CNHDEPO_2` — `rawmdGetYieldCurve2` vs `McpYieldCurve2` VP  
- **Compare_FXFP2**：`USDCNH_FXFP_BGN_2` — RawMD vs Direct  

Diff 列应接近 0 bp（数量级一致）。

## **主要函数**

| RawMD | Direct | 读数 |
|-------|--------|------|
| [rawmdGetYieldCurve2](/zh/latest/api/rawmarketdata.html) | [McpYieldCurve2](/zh/latest/api/yieldcurve.html) | [YieldCurve2ZeroRate](/zh/latest/api/yieldcurve.html) |
| [rawmdGetFXForwardPointsCurve2](/zh/latest/api/rawmarketdata.html) | [McpFXForwardPointsCurve2](/zh/latest/api/fxforwardratecurve.html) | [Fxfpc2FXSpotRate](/zh/latest/api/fxforwardratecurve.html) |

## **排错**

- MarketDataRoot 设为 `data/market_data`（相对工作簿）
- PillarData 由生成脚本从 JSON 填充，勿手工改 Bid/Ask 列
