# **Swap Strategy Case Study**


> Visit the Mathema Option Pricing System for foreign exchange options and structured product valuation!
[![Visit the Mathema Option Pricing System for foreign exchange options and structured product valuation!](../pic/mathema.png)](https://fxo.mathema.com.cn)

The swap strategy provides functions such as cash flow analysis, risk indicator analysis (e.g., NPV, duration, market value, etc.), and curve analysis for cross-period strategies, basis strategies, and butterfly strategies related to structures like FROO7 and SHIBOR3M.
Click the image below to download the template:

---
[![MCP-TC25-Swap Strategy](./pic/tc25.png)](./MCP-TC25-SwapStrategy.xlsx)
---

## **Instructions for Using the Function of the Swap Strategy Case Template**

### **1. Holiday Calendar Construction Functions**
- **[McpCalenders](/latest/api/calendar.html#excel-mcpcalenders-ccy)**：Constructs a holiday calendar object.

### **2. SwapCurve Construction Functions**
- **[McpVanillaSwapCurveData](/latest/api/yieldcurve.html#excel-mcpvanillaswapcurvedata-args-data)**：Construct a Vanilla Swap Curve object.
- **[McpSwapCurve](/latest/api/yieldcurve.html#excel-mcpswapcurve-args1-args2-args3-args4-args5-fmt-vp)**：Construct a Swap Curve object.

### **3. IRS Construction Functions**
- **[McpVanillaSwap](/latest/api/vanillaswap.html#excel-mcpvanillaswap-args1-args2-args3-args4-args5-fmt-vp)**: Constructs an IRS object.

### **4. Fixed Leg Analysis Functions**
- **[SwapFixedLegAnnuity](/latest/api/vanillaswap.html#excel-swapfixedlegannuity-vanillaswap)**: Calculates the annuity.
- **[SwapFixedLegDuration](/latest/api/vanillaswap.html#excel-swapfixedlegduration-vanillaswap)**: Calculates the duration.
- **[SwapFixedLegMDuration](/latest/api/vanillaswap.html#excel-swapfixedlegmduration-vanillaswap)**: Calculates the modified duration.
- **[SwapFixedLegCumPV](/latest/api/vanillaswap.html#excel-swapfixedlegcumpv-vanillaswap)**: Calculates the cumulative present value.
- **[SwapFixedLegCumCF](/latest/api/vanillaswap.html#excel-swapfixedlegcumcf-vanillaswap)**: Calculates the cumulative cash flow.
- **[SwapFixedLegNPV](/latest/api/vanillaswap.html#excel-swapfixedlegnpv-vanillaswap)**: Calculates the net present value (NPV).
- **[SwapFixedLegDV01](/latest/api/vanillaswap.html#excel-swapfixedlegdv01-vanillaswap)**: Calculates the DV01.
- **[SwapFixedLegPremium](/latest/api/vanillaswap.html#excel-swapfixedlegpremium-vanillaswap)**: Calculates the premium.
- **[SwapFixedLegAccrued](/latest/api/vanillaswap.html#excel-swapfixedlegaccrued-vanillaswap)**: Calculates the accrued interest.
- **[SwapFixedLegMarketValue](/latest/api/vanillaswap.html#excel-swapfixedlegmarketvalue-vanillaswap)**: Calculates the market value.

### **5. Floating Leg Analysis Functions**
- **[SwapFloatingLegAnnuity](/latest/api/vanillaswap.html#excel-swapfloatinglegannuity-vanillaswap)**: Calculates the annuity.
- **[SwapFloatingLegDuration](/latest/api/vanillaswap.html#excel-swapfloatinglegduration-vanillaswap)**: Calculates the duration.
- **[SwapFloatingLegMDuration](/latest/api/vanillaswap.html#excel-swapfloatinglegmduration-vanillaswap)**: Calculates the modified duration.
- **[SwapFloatingLegCumPV](/latest/api/vanillaswap.html#excel-swapfloatinglegcumpv-vanillaswap)**: Calculates the cumulative present value.
- **[SwapFloatingLegCumCF](/latest/api/vanillaswap.html#excel-swapfloatinglegcumcf-vanillaswap)**: Calculates the cumulative cash flow.
- **[SwapFloatingLegNPV](/latest/api/vanillaswap.html#excel-swapfloatinglegnpv-vanillaswap)**: Calculates the net present value (NPV).
- **[SwapFloatingLegDV01](/latest/api/vanillaswap.html#excel-swapfloatinglegdv01-vanillaswap)**: Calculates the DV01.
- **[SwapFloatingLegPremium](/latest/api/vanillaswap.html#excel-swapfloatinglegpremium-vanillaswap)**: Calculates the premium.
- **[SwapFloatingLegAccrued](/latest/api/vanillaswap.html#excel-swapfloatinglegaccrued-vanillaswap)**: Calculates the accrued interest.
- **[SwapFloatingLegMarketValue](/latest/api/vanillaswap.html#excel-swapfloatinglegmarketvalue-vanillaswap)**: Calculates the market value.

### **6. Swap Result Functions**
- **[SwapNPV](/latest/api/vanillaswap.html#excel-swapnpv-vanillaswap)**: Calculates the net present value (NPV).
- **[SwapMarketParRate](/latest/api/vanillaswap.html#excel-swapmarketparrate-vanillaswap)**: Calculates the Par Rate/Yield.
- **[SwapDuration](/latest/api/vanillaswap.html#excel-swapduration-vanillaswap)**: Calculates the duration.
- **[SwapMDuration](/latest/api/vanillaswap.html#excel-swapmduration-vanillaswap)**: Calculates the modified duration.
- **[SwapPV01](/latest/api/vanillaswap.html#excel-swappv01-vanillaswap)**: Calculates the PVBP.
- **[SwapDV01](/latest/api/vanillaswap.html#excel-swapdv01-vanillaswap)**: Calculates the DV01.
- **[SwapCF](/latest/api/vanillaswap.html#excel-swapcf-vanillaswap)**: Calculates the cash flow.
- **[SwapValuationDayCF](/latest/api/vanillaswap.html#excel-swapvaluationdaycf-vanillaswap)**: Calculates the valuation day cash flow.
- **[SwapMarketValue](/latest/api/vanillaswap.html#excel-swapmarketvalue-vanillaswap)**: Calculates the market value.
- **[SwapAccrued](/latest/api/vanillaswap.html#excel-swapaccrued-vanillaswap)**: Calculates the accrued interest.
- **[SwapPNL](/latest/api/vanillaswap.html#excel-swappnl-vanillaswap-start-end)**: Calculates the P&L.

