# **HistVol from CSV 案例**


> 访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！
[![访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！](../pic/mathema.png)](https://fxo.mathema.com.cn)

不依赖 JSON `HistVol` 节点：按 `price_data_index` 读与快照同目录的 HIST CSV，动态构建 `McpHistVols`，再用 `HvsGetVol` 读年化波动率。

**功能描述：** LiveStore / RawMD 两表对同一 CSV（USDCNH、EURUSD，窗口 60，EWMA）取对象并读数，便于对照。

[下载 MCP-TC42-HistVolFromCSV.xlsx](./MCP-TC42-HistVolFromCSV.xlsx)

## **对象链**

1. `=McpLiveMarketDataStore("data/market_data/MCP_MARKET_DATA_20260810.json")`  
2. `=mdlsHistVolFromPriceData(Store,"FXSPOT","USDCNH",估值日,60,"EWMA")` → `McpHistVols@n`  
3. `=HvsGetVol(对象, 估值日, 60)`  

RawMD 对照：`=McpRawMarketManager("data/market_data")` → `rawmdHistVolFromPriceData`

CSV：`data/market_data/FX_SPOT_PRICES_HIST.csv`（须与快照同目录）

## **主要函数**

| 函数 | 说明 |
|------|------|
| [mdlsHistVolFromPriceData](/zh/latest/api/rawmarketdata.html) | LiveStore 从 CSV 构建 HistVol |
| [rawmdHistVolFromPriceData](/zh/latest/api/rawmarketdata.html) | RawMD 同口径 |
| [HvsGetVol](/zh/latest/api/histvol.html) | 读年化 σ |

## **Python 示例**

完整示例：`example/market_data/histvol_csv_demo.py`

## **排错**

- `#NAME?`：注册 `mcp_market_data_live`、`mcp_raw_market_data` 并 Reload PyXLL
- CSV 找不到：确认与 JSON 同目录，且 `price_data_index.FXSPOT.hist_file` 为 `FX_SPOT_PRICES_HIST.csv`
- instrument_code 须与 CSV 列一致（`USDCNH` / `EURUSD`）
