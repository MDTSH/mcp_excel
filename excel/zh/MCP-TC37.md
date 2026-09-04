# **交叉货币基差曲线案例**


> 访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！
[![访问猛犸期权定价系统，支持外汇期权和结构化产品定价估值！](../pic/mathema.png)](https://fxo.mathema.com.cn)

独立样例 JSON（不走 `MCP_MARKET_DATA` 主索引）：KV Direct（Path A2 / Path B）与 `McpXccyBasisCurveFromJson`。

## **功能描述**

演示交叉货币基差曲线的独立样例（不走 `MCP_MARKET_DATA` 主索引）：KV Direct Path A2（引用已有 FXFP）与 Path B（`BasisSpreads`），以及 `McpXccyBasisCurveFromJson`。

数据：`data/XCCY_BASIS_CURVE_SAMPLE.json`（相对工作簿，经 `McpResolvePath`）。主要 Sheet：`KV_Direct`（flat 输入曲线 + Path A2/B + DF/spread 校验）、`FromJson`（同 curve_id 从 JSON 加载）。F9 后可用 `XccyBasisCurveDiscountFactor` / `XccyBasisCurveSpread` 读数；硬校验看 DF / SpotSpr_bp。

> **打开即可用**：请下载 [TC31–TC46 完整案例包](/download/MCP-TC31-46-LiveStoreRawMD.zip)（含全部工作簿和共用的 `data/`）。解压后打开 `zh` 目录里的 xlsx。只下单个工作簿时，必须把包里的 `data` 文件夹放到与 xlsx **同一目录**。

[下载 MCP-TC37-XccyBasis.xlsx](./MCP-TC37-XccyBasis.xlsx)

## **对象链**

1. `=McpYieldCurve` / `=McpFXForwardPointsCurve` VP 构造输入曲线  
2. `=McpXccyBasisCurve(...)` Path A2（引用 FXFP）或 Path B（BasisSpreads）  
3. `=McpXccyBasisCurveFromJson(McpResolvePath("data/XCCY_BASIS_CURVE_SAMPLE.json"), curve_id, usd, cny, fxfp)`  
4. `=XccyBasisCurveDiscountFactor` / `XccyBasisCurveSpread`

样例：`data/XCCY_BASIS_CURVE_SAMPLE.json`（相对工作簿）

## **主要函数**

| 函数 | 说明 |
|------|------|
| McpXccyBasisCurve | KV VP 构造 |
| McpXccyBasisCurveFromJson | 从独立 JSON 加载 |
| XccyBasisCurveDiscountFactor | 读 DF |
| XccyBasisCurveSpread | 读 spread（ref 锚定） |

## **Python 示例**

见 `excel/test_xccy_basis_curve.py`（与 C++ fixture 对照）。本案例不使用 `excel/data/market_data/` 主快照。

## **排错**

- JSON 路径用相对工作簿 + `McpResolvePath`，勿写盘符绝对路径
- FXFP 必须带 Calendar，否则 Missing fields: Calendar
- 长端 Spread UDF 为 ref 锚定，硬校验用 DF / SpotSpr_bp
