# FR007-10Y FR007-1M FR007-1Y FR007-2Y FR007-3M FR007-3Y FR007-4Y FR007-5Y FR007-6M FR007-7Y FR007-9M
# SHIBOR3M_10Y SHIBOR3M_1Y SHIBOR3M_2Y SHIBOR3M_3Y SHIBOR3M_4Y SHIBOR3M_5Y SHIBOR3M_6M SHIBOR3M_7Y SHIBOR3M_9M
from mcp.server_version import mcp_server


def test_irs():
    short_name = 'FR007-1Y'
    obj = mcp_server.McpVanillaSwaps2(short_name)
    swap_rate = obj[0][0].CalculateSwapRateFromNPV(0)
    mcp_server.McpVanillaSwaps2(short_name,'',swap_rate)
    print(swap_rate)

def main():
    test_irs()
    
if __name__ == "__main__":
    main()