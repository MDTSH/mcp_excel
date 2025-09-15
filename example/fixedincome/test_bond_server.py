from datetime import datetime

from mcp.server_version import mcp_server

def main():
    test_bond()

def test_bond():
    bond_code = '230023.IB'
    today = datetime.now().strftime("%Y/%m/%d")
    obj = mcp_server.McpBond(bond_code,today)
    print(obj)
    result = mcp_server.McpFixedRateBondsData(obj)
    mcp_server.decode(result)
    print(result)

if __name__ == "__main__":
    main()