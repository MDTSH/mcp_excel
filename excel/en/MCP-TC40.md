# **FX Vanilla LiveStore Case**


> Visit the Mathema Option Pricing System for FX options and structured-product valuation!
[![Visit the Mathema Option Pricing System](../pic/mathema.png)](https://fxo.mathema.com.cn)

Load `FXVolSurface2` from a standard `MCP_MARKET_DATA` JSON via LiveStore, then price a USD/CNH European vanilla with `McpVanillaOption` (VoType=10).

**What it does:** Config holds the relative snapshot path and trade fields; LiveStore returns the surface object; FXO定价 builds the option and shows Price / PV / Spot / Vol / Delta.

[Download MCP-TC40-FXVanillaLiveStore.xlsx](./MCP-TC40-FXVanillaLiveStore.xlsx)

## **Object chain**

1. `=McpLiveMarketDataStore("data/market_data/MCP_MARKET_DATA_20260810.json")`  
2. `=mdlsGetFXVolSurface2(Store,"USDCNH_RVOL_BGN_2")`  
3. `=McpVanillaOption(..., VoType=10)`  
4. `=McpPrice` / `McpPV` / `VOGetSpot`

JSON: `data/market_data/MCP_MARKET_DATA_20260810.json` (relative to the workbook, P0)

## **Key functions**

| Function | Description |
|----------|-------------|
| [McpLiveMarketDataStore](/latest/api/rawmarketdata.html) | Load snapshot |
| [mdlsGetFXVolSurface2](/latest/api/rawmarketdata.html) | FXVolSurface2 object |
| [McpVanillaOption](/latest/api/vanillaoption.html) | VoType=10 |

## **Python example**

See `example/market_data/fx_vanilla_livestore_demo.py`.

## **Troubleshooting**

- `#NAME?`: register `mcp_market_data_live` and Reload PyXLL
- Use relative path `data/market_data/…`
- Curve id must be `USDCNH_RVOL_BGN_2` (P0 has no USDCNY)
