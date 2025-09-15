"""
Get pre-built yield curves from server

Supported curve name explanations:
Naming rules:
- `Rev`: Represents end-of-day data (replay data).
- `Snap`: Represents real-time data (snapshot data).
- Curve types:
    - `BondCurve`: Bond curve.
    - `SwapCurve`: Swap curve.
    - `YldCurve`: Spot yield curve.
    - Currency pairs: e.g., `CNY` represents Chinese Yuan.

Supported curves include:
1. CNYTRYRevBondCurve: Chinese Yuan government bond end-of-day curve (end-of-day data).
2. CNHShibor3mRevSwapCurve: Offshore Chinese Yuan Shibor 3-month swap curve (end-of-day data).
3. CNHTRYRevBondCurve: Offshore Chinese Yuan bond curve (end-of-day data).
4. USDLiborrRevSwapCurve: USD Libor swap curve (end-of-day data).
5. USDSofrRevYldCurve: USD SOFR yield curve (end-of-day data).
6. CNYFR007SnapSwapCurve: Chinese Yuan FR007 swap curve (real-time data).
7. WINDCNYFR007SwapCurve: Chinese Yuan FR007 swap curve (Wind data).
8. BTCUSDTRateCurve: Bitcoin implied interest rate curve.
9. ETHUSDTRateCurve: Ethereum implied interest rate curve.
More interest rate curves as follows:
# CNYTRYRevBondCurve CNHShibor3mRevSwapCurve CNHTRYRevBondCurve USDLiborrRevSwapCurve USDSofrRevYldCurve CNYFR007SnapSwapCurve
# CNYTRYSnapBondCurve CNHFR007SnapSwapCurve CNHTRYSnapBondCurve USDLiborrSnapSwapCurve CNHShibor3mSnapSwapCurve CNHFR007RevSwapCurve
# EURDepoSnapYldCurve EURDepoRevYldCurve USDSofrSnapYldCurve USDDepoRevYldCurve USDDepoSnapYldCurve CNHShibor3mSnapYldCurve CNYRiskFreeRateCurve
# CNYShibor3mSnapSwapCurve CNYShibor3mRevSwapCurve CNYFR007RevSwapCurve CNYShibor3mSnapYldCurve WINDCNYFR007SwapCurve BTCUSDTRateCurve ETHUSDTRateCurve


"""

from mcp.server_version import mcp_server
from mcp.wrapper import McpSwapCurve
from mcp.tools import McpCalendar
from mcp.utils.enums import DayCounter, Frequency


def test_mcpswapcurves_demo_with_mid():
    """
    Test the functionality of getting swap curves, example: CNYTRYRevBondCurve.
    """
    # Define short name and reference date
    reference_date = '2025-08-11'
    short_name = 'CNYTRYRevBondCurve'

    # Get swap curve object
    swap_curve: McpSwapCurve = mcp_server.McpSwapCurves(short_name)

    # Print basic information
    print(f"Successfully loaded curve: {short_name}")
    print(f"Reference Date: {reference_date}")

    # Create calendar object
    cal = McpCalendar()

    # Calculate start date and future time points (1M, 3M, 6M)
    value_date = cal.ValueDate(reference_date)
    tenor_to_date = {
        '1M': cal.AddPeriod(value_date, "1M"),  # 1 month later
        '3M': cal.AddPeriod(value_date, "3M"),  # 3 months later
        '6M': cal.AddPeriod(value_date, "6M"),  # 6 months later
    }
    # Forward dates after 3M
    tenor_forward_date = {
        '1M': cal.AddPeriod(cal.AddPeriod(value_date, "1M"), "3M"),  # 1 month later + 3 months
        '3M': cal.AddPeriod(cal.AddPeriod(value_date, "3M"), "3M"),  # 3 months later + 3 months
        '6M': cal.AddPeriod(cal.AddPeriod(value_date, "6M"), "3M"),  # 6 months later + 3 months
    }
    # Print swap curve data
    print("Swap Curve Points:")
    for tenor, date in tenor_to_date.items():
        discount_factor = swap_curve.DiscountFactor(date)  # Get swap rate
        zero_rate = swap_curve.ZeroRate(date)  # Get swap rate
        forward_date = tenor_forward_date[tenor]
        compounding = True
        forward_rate = swap_curve.ForwardRate(date, forward_date, DayCounter.Act365Fixed, compounding, Frequency.Annual)  # Get swap rate
        print(f"{date}: Tenor {tenor} → Discount Factor: {discount_factor:.4f} → Zero Rate: {zero_rate:.4f} → Forward Rate: {forward_rate:.4f}")

# Test program entry point
if __name__ == "__main__":
    test_mcpswapcurves_demo_with_mid()