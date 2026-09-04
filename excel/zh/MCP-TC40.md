# **FX Vanilla LiveStore 案例**


> 访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！
[![访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！](../pic/mathema.png)](https://fxo.mathema.com.cn)

从标准 `MCP_MARKET_DATA` JSON 经 LiveStore 取 `FXVolSurface2`，再用已有 `McpVanillaOption`（VoType=10）对 USD/CNH 欧式香草定价。

**功能描述：** Config 填写相对路径快照与要素；LiveStore 表取曲面对象；FXO定价表构造期权并输出 Price / PV / Spot / Vol / Delta。

> **打开即可用**：请下载 [TC31–TC46 完整案例包](/download/MCP-TC31-46-LiveStoreRawMD.zip)（含全部工作簿和共用的 `data/`）。解压后打开 `zh` 目录里的 xlsx。只下单个工作簿时，必须把包里的 `data` 文件夹放到与 xlsx **同一目录**。

[下载 MCP-TC40-FXVanillaLiveStore.xlsx](./MCP-TC40-FXVanillaLiveStore.xlsx)

## **对象链**

1. `=McpLiveMarketDataStore("data/market_data/MCP_MARKET_DATA_20260810.json")`  
2. `=mdlsGetFXVolSurface2(Store,"USDCNH_RVOL_BGN_2")` → `McpFXVolSurface2@n`  
3. `=McpVanillaOption(..., VoType=10)`  
4. `=McpPrice` / `McpPV` / `VOGetSpot` / `VOGetVol`

JSON：`data/market_data/MCP_MARKET_DATA_20260810.json`（相对工作簿，P0）

## **主要函数**

| 函数 | 说明 |
|------|------|
| [McpLiveMarketDataStore](/zh/latest/api/rawmarketdata.html) | 加载快照 |
| [mdlsGetFXVolSurface2](/zh/latest/api/rawmarketdata.html) | 取双边 FX 波动率曲面 |
| [McpVanillaOption](/zh/latest/api/vanillaoption.html) | VoType=10（FXVolSurface2 + Strike） |
| [McpPrice](/zh/latest/api/vanillaoption.html) | 期权费 |

## **Python 示例**

完整示例：`example/market_data/fx_vanilla_livestore_demo.py`

## **排错**

- `#NAME?`：注册 `mcp_market_data_live` 并 Reload PyXLL
- 路径用 `data/market_data/…`（相对工作簿）
- 曲面 ID 须为 `USDCNH_RVOL_BGN_2`（P0 无 USDCNY）
