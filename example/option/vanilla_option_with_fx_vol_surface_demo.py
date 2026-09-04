#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FX Vanilla Option pricing demo using a single-sided FX volatility surface (``McpFXVolSurface``).

This script showcases how to:
1. Build single-sided yield curves (`McpYieldCurve`) from market quotes
2. Construct an FX forward points curve (`McpFXForwardPointsCurve`)
3. Build a single-sided FX volatility surface (`McpFXVolSurface`)
4. Price a vanilla FX option by directly invoking the native constructor
   ``MVanillaOption(callPut, referenceDate, expiryDate, deliveryDate, strike,
   fxVolSurface, premiumDate, buySell, faceValue)``
5. Retrieve key pricing outputs (price and deltas) and inspect option state fields

Author: Mathema Team
Version: 2.1
Last Updated: November 2025
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

import mcp.mcp
from mcp.utils.enums import (
    EnumWrapper,
    BuySell,
    CallPut,
    CalculatedTarget,
    DateAdjusterRule,
    DayCounter,
    DeltaType,
    InterpolationMethod,
    SmileInterpMethod,
)
from example.calendar.calendar_demo import (
    McpNCalendar,
    GetCurrencyCalendar,
    usd_dates,
    cny_dates,
)
from mcp.tool.tools_main import (
    McpFXForwardPointsCurve,
    McpFXVolSurface,
    McpYieldCurve,
)

# ==================== Global Configuration ====================
REFERENCE_DATE = "2024-12-13"
EXPIRY_DATE = "2025-02-14"
DELIVERY_DATE = "2025-02-18"
PREMIUM_DATE = "2024-11-18"
PAIR = "USD/CNY"
STRIKE_PX = 7.3
FACE_AMOUNT = 1_000_000.0
FX_SPOT_BID = 7.2768
FX_SPOT_ASK = 7.2770

CALENDAR = McpNCalendar(["USD", "CNY"], [usd_dates, cny_dates])
USD_CAL = GetCurrencyCalendar("USD", usd_dates)
CNY_CAL = GetCurrencyCalendar("CNY", cny_dates)
WRAPPER = EnumWrapper()

# ==================== Market Quotes ====================
USD_TENORS = [
    "ON",
    "TN",
    "SN",
    "SW",
    "2W",
    "3W",
    "1M",
    "2M",
    "3M",
    "4M",
    "5M",
    "6M",
    "7M",
    "8M",
    "9M",
    "10M",
    "11M",
    "1Y",
    "2Y",
    "3Y",
    "4Y",
    "5Y",
]
USD_ZERO_BID = [
    0.0458,
    0.04389,
    0.04500,
    0.04389,
    0.04330,
    0.04600,
    0.04330,
    0.04330,
    0.04330,
    0.04350,
    0.04350,
    0.04330,
    0.04340,
    0.04340,
    0.04330,
    0.04330,
    0.04330,
    0.04330,
    0.04400,
    0.04300,
    0.04200,
    0.04200,
]
CNY_TENORS = ["ON", "1W", "2W", "1M", "3M", "6M", "9M", "1Y"]
CNY_ZERO_BID = [
    0.01403,
    0.01758,
    0.01870,
    0.01710,
    0.01735,
    0.01744,
    0.01758,
    0.01774,
]
FORWARD_TENORS = [
    "SW",
    "2W",
    "3W",
    "1M",
    "2M",
    "3M",
    "4M",
    "5M",
    "6M",
    "7M",
    "8M",
    "9M",
    "10M",
    "11M",
    "1Y",
    "18M",
    "2Y",
    "3Y",
    "4Y",
    "5Y",
]
FORWARD_POINTS_BID = [
    -39.5,
    -77.0,
    -116.0,
    -177.0,
    -360.35,
    -522.77,
    -709.23,
    -922.0,
    -1124.52,
    -1328.0,
    -1531.0,
    -1749.28,
    -1940.0,
    -2145.0,
    -2388.0,
    -3450.0,
    -4330.0,
    -5696.61,
    -6000.0,
    -8050.0,
]
BID_VOL_TABLE = (
    "0.05131,0.049980,0.04865,0.04734,0.04602,0.04478,0.04360,0.04258,0.04174,0.04108,0.04062,0.040350,0.04026,0.04034,0.04058,0.04092,0.04131;"
    "0.05284,0.05215,0.05141,0.05046,0.04935,0.0482,0.04707,0.04605,0.04525,0.04462,0.04424,0.04409,0.04417,0.04448,0.0449,0.04534,0.04584;"
    "0.05459,0.05368,0.05274,0.05171,0.05059,0.04942,0.0483,0.04727,0.0465,0.04586,0.04549,0.04534,0.04541,0.045720,0.04623,0.04687,0.04759;"
    "0.05407,0.0529,0.05175,0.05064,0.04962,0.0487,0.04792,0.04734,0.047,0.04686,0.04694,0.04721,0.04763,0.04815,0.04875,0.04940,0.05006;"
    "0.05753,0.05701,0.05644,0.05583,0.05513,0.05443,0.05382,0.05339,0.05325,0.05337,0.05379,0.05445,0.05531,0.05631,0.05740,0.05857,0.059770;"
    "0.05405,0.05314,0.052270,0.05146,0.05076,0.05021,0.04988,0.04982,0.05,0.05054,0.05136,0.05235,0.05341,0.05445,0.05538,0.05624,0.05705;"
    "0.057460,0.05686,0.056280,0.05574,0.05527,0.05492,0.05477,0.05489,0.05518,0.05586,0.05684,0.05803,0.05932,0.06065,0.06193,0.06317,0.0644;"
    "0.0592,0.05875,0.05831,0.0579,0.05753,0.05729,0.05722,0.05744,0.05776,0.05849,0.05956,0.06084,0.06225,0.06371,0.06516,0.06659,0.068;"
    "0.06030,0.05995,0.0596,0.05926,0.05897,0.05878,0.05878,0.05905,0.05937,0.06014,0.06126,0.0626,0.06408,0.06563,0.06718,0.06873,0.07026;"
    "0.06064,0.06007,0.05956,0.05915,0.05891,0.05885,0.05902,0.05945,0.05975,0.0605,0.06161,0.06299,0.06459,0.0664,0.06837,0.07044,0.07254;"
    "0.06039,0.05996,0.05961,0.05933,0.05918,0.05921,0.05944,0.05991,0.06011,0.06078,0.06186,0.06324,0.06492,0.06691,0.06919,0.07166,0.07421;"
    "0.05928,0.05884,0.05844,0.05817,0.058070,0.05819,0.05856,0.05918,0.05924,0.05980,0.06089,0.06227,0.06399,0.06602,0.06838,0.07091,0.07351;"
    "0.05803,0.05756,0.05716,0.056870,0.05673,0.05682,0.05719,0.05789,0.05775,0.05819,0.05939,0.06093,0.06280,0.06498,0.06741,0.07002,0.07267"
)

DELTA_STRINGS = [
    "10DPUT",
    "15DPUT",
    "20DPUT",
    "25DPUT",
    "30DPUT",
    "35DPUT",
    "40DPUT",
    "45DPUT",
    "ATM",
    "45DCAL",
    "40DCAL",
    "35DCAL",
    "30DCAL",
    "25DCAL",
    "20DCAL",
    "15DCAL",
    "10DCAL",
]

TENORS_FOR_VOL = [
    "SW",
    "2W",
    "3W",
    "1M",
    "2M",
    "3M",
    "4M",
    "5M",
    "6M",
    "9M",
    "1Y",
    "18M",
    "2Y",
]


# ==================== Builders ====================
def build_yield_curves() -> Tuple[Any, Any]:
    """Build single-sided USD and CNY yield curves."""
    usd_curve = McpYieldCurve(
        {
            "ReferenceDate": REFERENCE_DATE,
            "Tenors": USD_TENORS,
            "ZeroRates": USD_ZERO_BID,
            "Method": InterpolationMethod.LINEARINTERPOLATION,
            "Calendar": USD_CAL,
            "DayCounter": DayCounter.Act365Fixed,
        }
    )

    cny_curve = McpYieldCurve(
        {
            "ReferenceDate": REFERENCE_DATE,
            "Tenors": CNY_TENORS,
            "ZeroRates": CNY_ZERO_BID,
            "Method": InterpolationMethod.LINEARINTERPOLATION,
            "Calendar": CNY_CAL,
            "DayCounter": DayCounter.Act365Fixed,
        }
    )

    return usd_curve, cny_curve


def build_forward_curve() -> Any:
    """Construct an FX forward points curve from single-sided data."""
    return McpFXForwardPointsCurve(
        {
            "ReferenceDate": REFERENCE_DATE,
            "Tenors": FORWARD_TENORS,
            "FXForwardPoints": FORWARD_POINTS_BID,
            "FXSpotRate": FX_SPOT_BID,
            "Method": InterpolationMethod.LINEARINTERPOLATION,
            "Calendar": CALENDAR,
            "ScaleFactor": 10000.0,
        }
    )


def build_vol_surface(yc_usd: Any, yc_cny: Any, forward_curve: Any) -> Any:
    """Build the single-sided FX volatility surface."""
    return McpFXVolSurface(
        {
            "ReferenceDate": REFERENCE_DATE,
            "SpotPx": FX_SPOT_BID,
            "Tenors": TENORS_FOR_VOL,
            "DeltaStrings": DELTA_STRINGS,
            "Volatilities": BID_VOL_TABLE,
            "ForeignCurve": yc_usd,
            "DomesticCurve": yc_cny,
            "Calendar": CALENDAR,
            "DateAdjusterRule": DateAdjusterRule.ModifiedFollowing,
            "DeltaType": DeltaType.FORWARD_DELTA,
            "SmileInterpMethod": SmileInterpMethod.CUBICSPLINE,
            "FxForwardPointsCurve": forward_curve,
            "PremiumAdjusted": False,
            "IsATMFwd": True,
            "SpotDate": REFERENCE_DATE,
            "CalculatedTarget": CalculatedTarget.CCY1,
            "Pair": PAIR,
        }
    )


# ==================== Option Pricing ====================
def price_option(fx_vol_surface: Any) -> Dict[str, Any]:
    """Price the vanilla option using the single-sided FX volatility surface."""
    vanilla_option = mcp.mcp.MVanillaOption(
        REFERENCE_DATE,
        EXPIRY_DATE,
        DELIVERY_DATE,
        STRIKE_PX,
        CallPut.Call,
        fx_vol_surface.getHandler(),
        PREMIUM_DATE,
        BuySell.Buy,
        FACE_AMOUNT,
    )

    price = vanilla_option.Price(True)
    delta_usd = vanilla_option.Delta(False, True)
    delta_cny = vanilla_option.Delta(True, True)

    details = {
        "ReferenceDate": vanilla_option.GetReferenceDate(),
        "SpotPx": vanilla_option.GetSpot(),
        "StrikePx": vanilla_option.GetStrike(),
        "BuySell": WRAPPER.key_of_value(vanilla_option.GetBuySell(), "BuySell"),
        "CallPut": WRAPPER.key_of_value(vanilla_option.GetCallPutType(), "CallPut"),
        "ExpiryDate": vanilla_option.GetExpiryDate(),
        "DeliveryDate": vanilla_option.GetDeliveryDate(),
        "TimeToExpiry": vanilla_option.GetTimeToExpiry(),
        "DomesticRate": vanilla_option.GetAccRate(),
        "ForeignRate": vanilla_option.GetUndRate(),
        "ForwardPx": vanilla_option.GetForward(),
        "Volatility": vanilla_option.GetVol(),
    }

    return {
        "price": price,
        "delta_usd": delta_usd,
        "delta_cny": delta_cny,
        "details": details,
    }


# ==================== Main Program ====================
def main() -> bool:
    print("=" * 60)
    print(" FX Vanilla Option Pricing Test (Single-Sided Vol Surface) ")
    print("=" * 60)

    try:
        # 1. Build market data inputs
        usd_curve, cny_curve = build_yield_curves()
        forward_curve = build_forward_curve()
        fx_vol_surface = build_vol_surface(usd_curve, cny_curve, forward_curve)

        # 2. Price the option
        results = price_option(fx_vol_surface)

        # 3. Output results
        print("\nPricing Results:")
        print(f"Price (amount): {results['price']}")
        print(f"Delta USD (isCCY2=False): {results['delta_usd']}")
        print(f"Delta CNY (isCCY2=True):  {results['delta_cny']}")

        print("\nOption State Details:")
        for key, value in results["details"].items():
            print(f"  {key}: {value}")

        return True
    except Exception as exc:  # pragma: no cover - diagnostic output for demo runs
        print(f"\nExecution failed: {exc}")
        return False


if __name__ == "__main__":
    success = main()
    if not success:
        import sys

        sys.exit(1)