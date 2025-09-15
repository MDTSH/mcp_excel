from mcp.tools import McpCalendar, McpVersion

def main():
    """Main function to demonstrate MCP calendar and version functionality"""
    print("MCP Quick Start Demo")
    print("=" * 40)
    
    # Create calendar object
    calendar = McpCalendar()
    date = calendar.ValueDate('2025-08-11')
    
    # Get MCP version
    version = McpVersion()
    
    # Print results
    print("MCP Python version:", version)
    print("MCP Python calendar works!")
    print("Value date for 2025-08-11:", date)
    print("Demo completed successfully!")

if __name__ == "__main__":
    main()