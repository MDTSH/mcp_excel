# **JsonReader 只读案例**


> 访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！
[![访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！](../pic/mathema.png)](https://fxo.mathema.com.cn)

单文件只读加载，与 LiveStore 同一 JSON；**不支持** patch。

> **打开即可用**：请下载 [TC31–TC46 完整案例包](/download/MCP-TC31-46-LiveStoreRawMD.zip)（含全部工作簿和共用的 `data/`）。解压后打开 `zh` 目录里的 xlsx。只下单个工作簿时，必须把包里的 `data` 文件夹放到与 xlsx **同一目录**。

[下载 MCP-TC34-MarketDataJsonReader.xlsx](./MCP-TC34-MarketDataJsonReader.xlsx)

## **对象链**

`McpMarketDataJsonReader(配置!B2)` → `mdjsonGetYieldCurve2` → `YieldCurve2ZeroRate`

## **主要函数**

| 函数 | 说明 |
|------|------|
| [McpMarketDataJsonReader](/zh/latest/api/rawmarketdata.html#excel-mcpmarketdatajsonreader-json-file) | 只读 Reader |
| [mdjsonGetYieldCurve2](/zh/latest/api/rawmarketdata.html#excel-mdjsongetyieldcurve2-reader-curve-id) | 取 YC2 对象 |

## **Python 示例**

```python
reader = mcp.MMarketDataJsonReader()
reader.loadFromFile(json_path)
yc2 = reader.getYieldCurve2("CNHDEPO_2")
print(yc2.ZeroRate("2026/08/10", "MID"))
```

见 `example/market_data/json_reader_demo.py`

## **与 TC31 区别**

| | LiveStore (TC31) | JsonReader (TC34) |
|--|------------------|-------------------|
| patch | 支持 | **不支持** |
| 适用 | 日内更新 / DoD | 静态快照只读 |
