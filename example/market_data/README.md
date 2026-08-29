# Market Data Manager 示例

标准 JSON 样例位于 `excel/data/market_data/`：

| 文件 | 说明 |
|------|------|
| `MCP_MARKET_DATA_20260810.json` | P0 脱敏主快照（CNHDEPO_2、USDCNH_FXFP_BGN_2、USDCNH_RVOL_BGN_2；含 FXSPOT `price_data_index`） |
| `MCP_MARKET_DATA_20260626.json` | P1 快照（Cross FXFP2 / Implied YC / FR007 / BondCurve） |
| `MCP_MARKET_DATA_P2_LOCALVOL_20260810.json` | P2 裁剪（EURUSD_LOCALVOL / CNYDEPO / EURDEPO） |
| `MCP_MARKET_DATA_20260827.json` | P3 小样（Credit / BondSpread / Forward / Vol） |
| `FX_SPOT_PRICES_HIST.csv` | P2 小样 HIST（USDCNH / EURUSD，与快照同目录） |
| `MCP_PATCH_CNHDEPO.json` | CNHDEPO_2 增量 patch |

## 三条入口对照

| 入口 | Python 类 | Excel UDF | 特点 |
|------|-----------|-----------|------|
| **LiveStore** | `MLiveMarketDataStore` | `McpLiveMarketDataStore` / `mdlsGet*` | 单文件 + 支持 `applyUpdate` |
| **RawMD** | `RawMarketDataManager` | `McpRawMarketManager` / `rawmdGet*` | 目录 + 估值日 |
| **JsonReader** | `MMarketDataJsonReader` | `McpMarketDataJsonReader` / `mdjsonGet*` | 单文件只读，不能 patch |

对象链（三条入口相同）：

```
JSON → Store/Manager/Reader → mdlsGet* / rawmdGet* / mdjsonGet*
     → McpYieldCurve2 / McpFXForwardPointsCurve2 / McpFXVolSurface2
     → YieldCurve2ZeroRate / Fxfpc2FXSpotRate / FXVolSurface2GetVolatility
```

## 运行

在项目根目录 `C:\mcp\mcpexcel1.4\python`：

```bash
python example/market_data/livestore_demo.py
python example/market_data/rawmd_demo.py
python example/market_data/json_reader_demo.py
python example/market_data/patch_dod_demo.py
python example/market_data/cross_fxfp2_demo.py
python example/market_data/implied_yc_demo.py
python example/market_data/fr007_rawmd_demo.py
python example/market_data/fx_vanilla_livestore_demo.py
python example/market_data/localvol_demo.py
python example/market_data/histvol_csv_demo.py
python example/market_data/creditcurve_demo.py
python example/market_data/bondspread_demo.py
python example/market_data/forwardcurve_demo.py
python example/market_data/volsurface_demo.py
```

Excel 测试用例：TC31–TC46（见 `excel/readme.md`）。工作簿在 VuePress `zh/latest/api/excel` 与 `latest/api/excel`（或从 [help Excel](https://help.mathema.com.cn/zh/latest/api/excel/) 下载），不要打开 `python/excel/MCP-TC*.xlsx`。

## P1 曲线示例

| 脚本 | 入口 | curve_id | 说明 |
|------|------|----------|------|
| `cross_fxfp2_demo.py` | **LiveStore** | `CNHTHB_FXFP_CROSS_2` | JSON 无 Tenors；Python RawMD 无法构建 Cross2 |
| `implied_yc_demo.py` | LiveStore + RawMD | `USDDEPO_IMPLIED` | FX 隐含 USD（CNHDEPO + USDCNH_FXFP_BGN） |
| `fr007_rawmd_demo.py` | C++ `MRawMarketManager` | `CNY_SWAP_FR007_BGN` | CalibrationSet 须走 C++（与 Excel `rawmdGetSwapCurve` 相同）；Python fromJson 无法 bootstrap |
| `fx_vanilla_livestore_demo.py` | LiveStore | `USDCNH_RVOL_BGN_2` | FX Vanilla VoType=10（TC40） |
| `localvol_demo.py` | LiveStore | `EURUSD_LOCALVOL` | TRC / TrippleRangesCall 用 LocalVol（TC41） |
| `histvol_csv_demo.py` | LiveStore + RawMD | `FXSPOT` / USDCNH | HIST CSV → `HvsGetVol`（TC42） |
| `creditcurve_demo.py` | LiveStore / C++ RawMD / JsonReader | `CNY_CREDIT_CFETS` | HazardRate / PD（TC43）；C++ 校准偶发失败则重试 / Python 兜底 |
| `bondspread_demo.py` | **C++ LiveStore** | `CNY_BOND_POLICY_SPREAD` | two_curves + `setBenchmark`(YieldCurve)；Python fromJson 失败（TC44） |
| `forwardcurve_demo.py` | LiveStore + C++ RawMD | `EQ_FORWARD` | 非 FX ForwardRate（TC45） |
| `volsurface_demo.py` | LiveStore + C++ RawMD | `EQ_VOL_SAMPLE` | 非 FX 2×5 网格（TC46） |

XccyBasis 不走本目录 JSON：见 `excel/test_xccy_basis_curve.py` 与 `excel/data/XCCY_BASIS_CURVE_SAMPLE.json`（TC37）。
