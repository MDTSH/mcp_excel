# **LiveStore 市场数据案例**


> 访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！
[![访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！](../pic/mathema.png)](https://fxo.mathema.com.cn)

从标准 `MCP_MARKET_DATA` JSON 加载 LiveStore，经 `mdlsGet*` 取曲线对象，再用 `YieldCurve2ZeroRate` 等读数；演示 `mdlsApplyUpdateFile` patch 与 Impact。

[下载 MCP-TC31-LiveStoreMarketData.xlsx](./MCP-TC31-LiveStoreMarketData.xlsx)

## **对象链**

1. `=McpLiveMarketDataStore(配置!B2)` → Store 句柄  
2. `=mdlsGetYieldCurve2(Store,"CNHDEPO_2")` → `McpYieldCurve2@n`  
3. `=YieldCurve2ZeroRate(曲线, 日期, "MID")`  
4. `=mdlsApplyUpdateFile(Store, patch路径)` **须被 patch 后读数引用**  
5. `=mdlsLastUpdateImpact(Store)` 查看 updated/affected

JSON / Patch 使用相对路径：`data/market_data/MCP_MARKET_DATA_20260810.json`、`MCP_PATCH_CNHDEPO.json`

## **主要函数**

| 函数 | 说明 |
|------|------|
| [McpLiveMarketDataStore](/zh/latest/api/rawmarketdata.html#excel-mcplivemarketdatastore-snapshot-file-or-dir) | 加载快照 |
| [mdlsGetYieldCurve2](/zh/latest/api/rawmarketdata.html#excel-mdlsgetyieldcurve2-store-curve-id) | 取 YieldCurve2 对象 |
| [mdlsApplyUpdateFile](/zh/latest/api/rawmarketdata.html#excel-mdlsapplyupdatefile-store-patch-file) | 增量 patch |
| [mdlsLastUpdateImpact](/zh/latest/api/rawmarketdata.html#excel-mdlslastupdateimpact-store) | Impact 表 |
| [YieldCurve2ZeroRate](/zh/latest/api/yieldcurve.html#excel-yieldcurve2zerorate-curve-date-bidmidask) | 从对象读零息 |

## **Python 示例**

```python
import os, sys
proj = r"C:\mcp\mcpexcel1.4\python"
sys.path[:0] = [proj, os.path.join(proj, "lib", "X64")]
import mcp.mcp as mcp

json_path = os.path.join(proj, "excel/data/market_data/MCP_MARKET_DATA_20260810.json").replace("\\", "/")
store = mcp.MLiveMarketDataStore()
store.loadSnapshot(json_path)
yc2 = store.getYieldCurve2("CNHDEPO_2")
print(yc2.ZeroRate("2026/08/10", "MID"))
store.applyUpdate(os.path.join(proj, "excel/data/market_data/MCP_PATCH_CNHDEPO.json"))
print(store.getYieldCurve2("CNHDEPO_2").ZeroRate("2026/08/10", "MID"))
```

完整示例：`example/market_data/livestore_demo.py`、`patch_dod_demo.py`

## **排错**

- `#NAME?`：检查 `pyxll.cfg` 含 `mcp_market_data_live`、`mcp_lifecycle`（最后）
- patch 无变化：`mdlsApplyUpdateFile` 须被 B14 及 patch 后 `mdlsGet*` 引用
- 路径错误：用 `=McpResolvePath(配置!B2)` 验证
