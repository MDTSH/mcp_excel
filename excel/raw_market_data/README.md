# Raw Market Data Python/Excel 集成

## 概述

本模块实现 **Raw Market Data** 在 Python/Excel 中的集成，从 `MCP_MARKET_DATA_YYYYMMDD.json` 主索引加载市场数据，构建 MCP 曲线/曲面对象，供 PyXLL Excel UDF 和批量估值使用。

**格式规范**：mathema-git `mcp-valuation-engine/docs/RAW_MARKET_DATA_JSON_DESIGN.md`

**继承与测试参考**：
- NEW_ASSET_CHECKLIST.md 十一-A（Python 继承体系）、十一-B（Python/Excel 测试清单）
- EXCEL_INTEGRATION_PITFALLS.md 五（Python 继承与测试注意事项）

---

## 目录结构

```
excel/raw_market_data/
├── __init__.py
├── raw_market_data_loader.py   # RawMarketDataIndex、RawMarketDataLoader、RawMarketDataManager
└── README.md
```

---

## 类说明

| 类 | 职责 |
|----|------|
| **RawMarketDataIndex** | 解析主索引 JSON，提供 curve_id、price_data_index 等只读访问 |
| **RawMarketDataLoader** | 从 JSON 构建 MCP 对象（YieldCurve、SwapCurve 等） |
| **RawMarketDataManager** | 目录管理、按 curve_id + valuation_date 查询 |

---

## 支持的数据类型

| 类型 | 构建方式 | 状态 |
|------|----------|------|
| **YieldCurve** | Tenors + ZeroRates → MYieldCurve；含 implied（FXFP + YC） | ✅ 已实现 |
| **YieldCurve2** | Tenors + Bid/AskZeroRates → MYieldCurve2 | ✅ 已实现 |
| **SwapCurve** | C++ `MRawMarketManager`（CalibrationSet）；Python `fromJson` 仅序列化格式 | ✅ Excel/C++（如 CNY_SWAP_FR007_BGN） |
| **BondCurve** | times_and_rates / fromJson → MBondCurve | ✅ 已实现（如 CNY_BOND_TREASURY） |
| **FXForwardPointsCurve** | Direct Pair 或 Cross Leg1/Leg2 | ✅ 已实现 |
| **FXForwardPointsCurve2** | Bid/Ask pillars；**Cross2 无 Tenors，须 LiveStore/C++ Manager** | ✅ Direct；Cross2 走 C++ |
| **FXVolSurface2** | fromJson | ✅ 已实现 |
| **VolSurface / LocalVol / HistVol** | 视快照 | 📋 按 JSON 节扩展 |

---

## 使用示例

### Python

```python
import sys
sys.path.insert(0, r"C:\mcp\mcpexcel1.4\python")

from excel.raw_market_data import RawMarketDataManager

# 设置市场数据根目录
manager = RawMarketDataManager(root=r"D:\market_data")
manager.set_root(r"D:\market_data")

# 按 curve_id + 日期获取曲线
yc = manager.get_yield_curve("CNY_ZERO", "2024-10-15")
if yc:
    print("ZeroRate 5Y:", yc.ZeroRate("2029-10-15"))
```

### Excel UDF

模块：`pyxll_func/custom/mcp_raw_market_data.py`、`mcp_market_data_live.py`

```
=McpRawMarketManager("data/market_data")
=rawmdGetYieldCurve2($B$1,"CNHDEPO_2","2026/08/10")
=rawmdAvailableDates($B$1)
=rawmdLatestValuationDate($B$1)

=McpLiveMarketDataStore("data/market_data/MCP_MARKET_DATA_20260810.json")
=mdlsGetYieldCurve2($B$1,"CNHDEPO_2")
=mdlsApplyUpdateFile($B$1,"data/market_data/MCP_PATCH_CNHDEPO.json")

=McpMarketDataJsonReader("data/market_data/MCP_MARKET_DATA_20260810.json")
=mdjsonGetYieldCurve2($B$1,"CNHDEPO_2")

=rawmdGetYieldCurve($B$1,"USDDEPO_IMPLIED","2026/06/26")
=rawmdGetSwapCurve($B$1,"CNY_SWAP_FR007_BGN","2026/06/26")
=rawmdGetBondCurve($B$1,"CNY_BOND_TREASURY","2026/06/26")
=rawmdGetFXForwardPointsCurve2($B$1,"CNHTHB_FXFP_CROSS_2","2026/06/26")
```

路径推荐相对工作簿；可用 `=McpResolvePath("data/market_data/…")` 解析。

Excel 案例：**TC31–TC46**（VuePress `zh/latest/api/excel` / `latest/api/excel`，或从 help 下载）。

P1 get*：`rawmdGetSwapCurve`、`rawmdGetBondCurve`、`rawmdGetYieldCurve`（implied）、`rawmdGetFXForwardPointsCurve2`（Cross 走 C++ Manager）。

P3 get*：`rawmdGetCreditCurve`、`rawmdGetBondSpreadCurve` + `rawmdBondSpreadSetBenchmark`（须 C++；benchmark 为 YieldCurve）、`rawmdGetForwardCurve`、`rawmdGetVolSurface`。

---

## Excel 集成检查（参考 EXCEL_INTEGRATION_PITFALLS）

新增 Raw Market Data 时需确认：

- [ ] **日期参数**：valuation_date 统一转为 YYYY-MM-DD
- [ ] **路径解析**：file_path 相对 config_base_dir 或绝对路径
- [ ] **M 类包装**：返回的曲线需为 McpYieldCurve、McpSwapCurve 等，供 Adapter 使用
- [ ] **Python 引用保持**：若 Adapter 持有曲线，需 `adapter._curve_ref = curve` 防 GC

---

## 测试

```
python excel/testcase/test_raw_market_data.py
```

---

## 相关文件

| 模块 | 路径 |
|------|------|
| 设计文档 | mcp-valuation-engine/docs/RAW_MARKET_DATA_JSON_DESIGN.md |
| 新增资产清单 | mcp-valuation-engine/docs/guide/NEW_ASSET_CHECKLIST.md |
| Excel 陷阱 | mcp-valuation-engine/docs/guide/EXCEL_INTEGRATION_PITFALLS.md |
| Excel UDF | pyxll_func/custom/mcp_raw_market_data.py |
| LiveStore UDF | pyxll_func/custom/mcp_market_data_live.py |
| Lifecycle (workbook close) | pyxll_func/core/mcp_lifecycle.py |
