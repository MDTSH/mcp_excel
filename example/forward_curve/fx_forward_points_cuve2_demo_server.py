"""
获取服务器端已经构建好的远期点数曲线

曲线名称解释：
命名规则：
- `Fwd`：Forward，表示远期曲线。
- `Snap`：实时数据（快照数据）。
- `Rev`：日终数据（复盘数据）。
- 货币对：表示相关的货币对，例如 `USDCNH` 表示美元对离岸人民币。

已经支持的远期曲线包括：
1. USDCNHFwdRevCurve: 美元对离岸人民币远期曲线（日终数据）。
2. USDCNYFwdRevCurve: 美元对在岸人民币远期曲线（日终数据）。
3. USDCNYFwdSnapCurve: 美元对在岸人民币远期曲线（实时数据）。
4. USDCNHFwdSnapCurve: 美元对离岸人民币远期曲线（实时数据）。
5. EURUSDFwdRevCurve: 欧元对美元远期曲线（日终数据）。
6. GBPUSDFwdRevCurve: 英镑对美元远期曲线（日终数据）。
7. EURUSDFwdSnapCurve: 欧元对美元远期曲线（实时数据）。
8. GBPUSDFwdSnapCurve: 英镑对美元远期曲线（实时数据）。
9. AUDUSDFwdSnapCurve: 澳元对美元远期曲线（实时数据）。
10. AUDUSDFwdRevCurve: 澳元对美元远期曲线（日终数据）。
11. USDCADFwdRevCurve: 美元对加元远期曲线（日终数据）。
12. USDCADFwdSnapCurve: 美元对加元远期曲线（实时数据）。
13. USDCHFFwdSnapCurve: 美元对瑞士法郎远期曲线（实时数据）。
14. USDCHFFwdRevCurve: 美元对瑞士法郎远期曲线（日终数据）。
15. USDJPYFwdRevCurve: 美元对日元远期曲线（日终数据）。
16. USDJPYFwdSnapCurve: 美元对日元远期曲线（实时数据）。
17. USDSGDFwdSnapCurve: 美元对新加坡元远期曲线（实时数据）。
18. EURCNYFwdSnapCurve: 欧元对在岸人民币远期曲线（实时数据）。
19. EURCNHFwdSnapCurve: 欧元对离岸人民币远期曲线（实时数据）。
"""

from mcp.server_version import mcp_server
from mcp.tools import McpCalendar
from mcp.wrapper import McpFXForwardPointsCurve2

def main():
    """Main function to demonstrate server-side FX forward points curve functionality"""
    print("FX Forward Points Curve Server Demo")
    print("=" * 50)
    
    try:
        # Server-side construction in just 2 lines!
        short_name = 'USDCNYFwdRevCurve'  # Predefined curve name on server
        curve: McpFXForwardPointsCurve2 = mcp_server.McpFXForwardPointsCurves2(short_name)  # Network call happens here

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
            bid_points = curve.FXForwardPoints(date,"BID")      
            bid_rate = curve.FXForwardOutright(date,"BID")      
            ask_points = curve.FXForwardPoints(date,"ASK")      
            ask_rate = curve.FXForwardOutright(date,"ASK")      
            print(f"{date}: {bid_points:.1f} pts → Rate: {bid_rate:.4f} → {ask_points:.1f} pts → Rate: {ask_rate:.4f}")
        
        print("Demo completed successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

if __name__ == "__main__":
    main()