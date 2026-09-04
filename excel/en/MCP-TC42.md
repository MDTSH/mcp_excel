# **HistVol from CSV Case**


> Visit the Mathema Option Pricing System for FX options and structured-product valuation!
[![Visit the Mathema Option Pricing System](../pic/mathema.png)](https://fxo.mathema.com.cn)

No JSON `HistVol` node: build `McpHistVols` from the HIST CSV listed in `price_data_index` (same folder as the snapshot), then read with `HvsGetVol`.

**What it does:** LiveStore and RawMD sheets use the same CSV (USDCNH / EURUSD, window 60, EWMA) so the two σ values can be compared.

> **Ready to run**: Download the [TC31–TC46 example pack](/download/MCP-TC31-46-LiveStoreRawMD.zip) (all workbooks plus shared `data/`). Unzip and open the xlsx under `en`. A single workbook will not run unless you place the pack's `data` folder next to it.

[Download MCP-TC42-HistVolFromCSV.xlsx](./MCP-TC42-HistVolFromCSV.xlsx)

## **Object chain**

1. `=McpLiveMarketDataStore("data/market_data/MCP_MARKET_DATA_20260810.json")`  
2. `=mdlsHistVolFromPriceData(Store,"FXSPOT","USDCNH",val_date,60,"EWMA")`  
3. `=HvsGetVol(object, val_date, 60)`  

RawMD: `=McpRawMarketManager("data/market_data")` → `rawmdHistVolFromPriceData`

CSV: `data/market_data/FX_SPOT_PRICES_HIST.csv` (must sit next to the snapshot)

## **Key functions**

| Function | Description |
|----------|-------------|
| [mdlsHistVolFromPriceData](/latest/api/rawmarketdata.html) | LiveStore HistVol from CSV |
| [rawmdHistVolFromPriceData](/latest/api/rawmarketdata.html) | RawMD same API |
| HvsGetVol | Annualized σ |

## **Python example**

See `example/market_data/histvol_csv_demo.py`.

## **Troubleshooting**

- `#NAME?`: register `mcp_market_data_live` / `mcp_raw_market_data` and Reload PyXLL
- CSV not found: keep it next to the JSON; `price_data_index.FXSPOT.hist_file` = `FX_SPOT_PRICES_HIST.csv`
- `instrument_code` must match the CSV (`USDCNH` / `EURUSD`)
