# 标准市场数据样例（P0 + P1 + P2 + P3）

本目录为 MCP Excel 发布包自带的**脱敏、裁剪**市场快照，供 Example / TC31–46 使用。

| 文件 | 说明 |
|------|------|
| `MCP_MARKET_DATA_20260810.json` | P0 主快照（YieldCurve / YieldCurve2 / FXFP2 / FXVol2 + FXSPOT price_data_index） |
| `MCP_MARKET_DATA_20260626.json` | P1 快照（Cross FXFP2 / Implied YC / FR007 / BondCurve） |
| `MCP_MARKET_DATA_P2_LOCALVOL_20260810.json` | P2 裁剪（EURUSD_LOCALVOL / CNYDEPO / EURDEPO / USDDEPO） |
| `MCP_MARKET_DATA_20260827.json` | P3 小样（Credit / BondSpread / Forward / Vol） |
| `FX_SPOT_PRICES_HIST.csv` | P2 小样 HIST（USDCNH / EURUSD，约 160 行） |
| `MCP_PATCH_CNHDEPO.json` | LiveStore 增量 patch（CNHDEPO_2 零息微调） |

## 包含 curve_id

P0（20260810）：

- `CNHDEPO`（YieldCurve）
- `CNHDEPO_2`、`USDDEPO_2`（YieldCurve2）
- `USDCNH_FXFP_BGN_2`（FXForwardPointsCurve2）
- `USDCNH_RVOL_BGN_2`（FXVolSurface2）
- `price_data_index.FXSPOT` → `FX_SPOT_PRICES_HIST.csv`

P2 LocalVol 文件：

- `CNYDEPO`、`EURDEPO`、`USDDEPO`（YieldCurve）
- `EURUSD_FXFP`、`USDCNY_FXFP_BGN`（FXForwardPointsCurve）
- `USDCNY_RVOL_BGN`（FXVolSurface v1）
- `EURUSD_LOCALVOL`（LocalVol）

P1（20260626）：

- `CNHDEPO`、`USDDEPO`、`USDDEPO_IMPLIED`（YieldCurve）
- `CNHDEPO_2`、`USDDEPO_2`（YieldCurve2）
- `USDCNH_FXFP_BGN`、`USDTHB_FXFP_BGN`、`CNHTHB_FXFP_CROSS`（FXForwardPointsCurve）
- `USDCNH_FXFP_BGN_2`、`USDTHB_FXFP_BGN_2`、`CNHTHB_FXFP_CROSS_2`（FXForwardPointsCurve2）
- `CNY_SWAP_FR007_BGN`（SwapCurve）
- `CNY_BOND_TREASURY`（BondCurve）

P3（20260827）：

- `CNYDEPO`、`CNYDEPO_BUMP`（YieldCurve；后者仅作 SetBenchmark）
- `CNY_CREDIT_CFETS`（CreditCurve，spreads BP）
- `CNY_BOND_TREASURY`、`CNY_BOND_POLICY`（BondCurve times_and_rates）
- `CNY_BOND_POLICY_SPREAD`（BondSpreadCurve two_curves；须 C++）
- `EQ_FORWARD`（ForwardCurve）
- `EQ_VOL_SAMPLE`（VolSurface 2×5）

## RawMD 目录用法

将 `McpRawMarketManager` 的 root 指向**本目录**（含 `MCP_MARKET_DATA_YYYYMMDD.json` 文件名）。

## LiveStore 用法

直接加载 JSON 文件路径，或指向含该文件的目录。
