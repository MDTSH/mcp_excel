"""
Get pre-built forward points curves from server

Curve name explanations:
Naming rules:
- `Fwd`: Forward, represents forward curve.
- `Snap`: Real-time data (snapshot data).
- `Rev`: End-of-day data (replay data).
- Currency pairs: Represents related currency pairs, e.g., `USDCNH` represents USD to offshore Chinese Yuan.

Supported forward curves include:
1. USDCNHFwdRevCurve: USD to offshore Chinese Yuan forward curve (end-of-day data).
2. USDCNYFwdRevCurve: USD to onshore Chinese Yuan forward curve (end-of-day data).
3. USDCNYFwdSnapCurve: USD to onshore Chinese Yuan forward curve (real-time data).
4. USDCNHFwdSnapCurve: USD to offshore Chinese Yuan forward curve (real-time data).
5. EURUSDFwdRevCurve: EUR to USD forward curve (end-of-day data).
6. GBPUSDFwdRevCurve: GBP to USD forward curve (end-of-day data).
7. EURUSDFwdSnapCurve: EUR to USD forward curve (real-time data).
8. GBPUSDFwdSnapCurve: GBP to USD forward curve (real-time data).
9. AUDUSDFwdSnapCurve: AUD to USD forward curve (real-time data).
10. AUDUSDFwdRevCurve: AUD to USD forward curve (end-of-day data).
11. USDCADFwdRevCurve: USD to CAD forward curve (end-of-day data).
12. USDCADFwdSnapCurve: USD to CAD forward curve (real-time data).
13. USDCHFFwdSnapCurve: USD to CHF forward curve (real-time data).
14. USDCHFFwdRevCurve: USD to CHF forward curve (end-of-day data).
15. USDJPYFwdRevCurve: USD to JPY forward curve (end-of-day data).
16. USDJPYFwdSnapCurve: USD to JPY forward curve (real-time data).
17. USDSGDFwdSnapCurve: USD to SGD forward curve (real-time data).
18. EURCNYFwdSnapCurve: EUR to onshore Chinese Yuan forward curve (real-time data).
19. EURCNHFwdSnapCurve: EUR to offshore Chinese Yuan forward curve (real-time data).
"""

from mcp.server_version import mcp_server
from mcp.tools import McpCalendar
from mcp.wrapper import McpFXForwardPointsCurve

def main():
    """Main function to demonstrate server-side FX forward points curve functionality"""
    print("FX Forward Points Curve Server Demo")
    print("=" * 50)
    
    try:
        # Server-side construction in just 2 lines!
        short_name = 'USDCNYFwdRevCurve'  # Predefined curve name on server
        curve: McpFXForwardPointsCurve = mcp_server.McpFXForwardPointsCurves(short_name)  # Network call happens here

        # Basic verification 
        print(f"Successfully loaded {short_name}")
        print("Sample forward points:")
        today = curve.GetReferenceDate()
        cal = McpCalendar()
        value_date = cal.ValueDate(today)

        tenor_to_date = {
            '1M': cal.AddPeriod(value_date, "1M"),  # 2025-09-11
            '3M': cal.AddPeriod(value_date, "3M"),  # 2025-11-11
            '6M': cal.AddPeriod(value_date, "6M"),  # 2026-02-11
        }

        for tenor, date in tenor_to_date.items():
            points = curve.FXForwardPoints(date)     
            rate = curve.FXForwardOutright(date)      
            print(f"{date}: {points:.1f} pts → Rate: {rate:.4f}")
        
        print("Demo completed successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

if __name__ == "__main__":
    main()