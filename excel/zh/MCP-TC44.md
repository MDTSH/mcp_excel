# **BondSpreadCurve 案例**


> 访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！
[![访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！](../pic/mathema.png)](https://fxo.mathema.com.cn)

从标准 JSON 的 `two_curves` 条目取债券利差曲线，读 `zeroSpread`，再用 `YieldCurve` 做基准冲击。

**功能描述：** `CNY_BOND_POLICY_SPREAD` = 国债 `CNY_BOND_TREASURY` 相对政策债 `CNY_BOND_POLICY`（均为小样 times_and_rates）。`rawmdBondSpreadSetBenchmark` 必须传入 `MYieldCurve`（样例 `CNYDEPO_BUMP`），不能传 BondCurve。须走 C++ LiveStore / Manager；Python fromJson 无法构建 two_curves。

[下载 MCP-TC44-BondSpreadCurve.xlsx](./MCP-TC44-BondSpreadCurve.xlsx)

## **对象链**

1. `=McpLiveMarketDataStore("data/market_data/MCP_MARKET_DATA_20260827.json")`  
2. `=mdlsGetBondSpreadCurve(Store,"CNY_BOND_POLICY_SPREAD")`  
3. `=BondSpreadCurveZeroSpread(曲线, 日期)`  
4. `=rawmdBondSpreadSetBenchmark(spread, mdlsGetYieldCurve(Store,"CNYDEPO_BUMP"))`

RawMD：`rawmdGetBondSpreadCurve` + `rawmdGetYieldCurve`

换基准后 ZeroRate 不变（调整后曲线未变），zeroSpread 会变。

## **主要函数**

| 函数 | 说明 |
|------|------|
| [mdlsGetBondSpreadCurve](/zh/latest/api/rawmarketdata.html) | LiveStore 取利差曲线 |
| [rawmdGetBondSpreadCurve](/zh/latest/api/rawmarketdata.html) | RawMD 取对象 |
| rawmdBondSpreadSetBenchmark | 替换基准（MYieldCurve） |
| BondSpreadCurveZeroSpread | 读零息利差 |

## **Python 示例**

完整示例：`example/market_data/bondspread_demo.py`

## **排错**

- `#NAME?`：注册 `mcp_market_data_live`、`mcp_raw_market_data` 并 Reload PyXLL
- `setBenchmarkCurve` 类型错误：第二参数须是 YieldCurve
- Python RawMD 返回空：请用 C++ Manager / LiveStore
