# MCP Core Pricing Engine Modules

## Module Overview

The `pyxll_func/core/` directory contains the core modules of the MCP pricing engine, providing pricing and risk calculation functions for various financial products. All modules have been standardized with unified code style and complete documentation comments.

## Directory Structure

```
pyxll_func/core/
├── bond.py                  # Bond pricing core module
├── option.py                # Option pricing core module
├── swap.py                  # Interest rate swap pricing core module
├── forward.py               # FX structured forward pricing core module
├── curve.py                 # Yield curve core module
├── volatility.py            # Volatility model core module
├── mcp_calendar.py          # Calendar utility module
├── mcp_server_mktdata.py    # Market data module
├── server_factory.py        # Server factory module
├── xscript.py               # Script execution module
├── quick_method.py          # Quick method module
└── utils.py                 # General utility module
```

## Module Function Description

### 1. Core Pricing Engine
- **bond.py**: Fixed rate bond pricing, including accrued interest, cash flow analysis, risk metrics calculation
- **option.py**: Option pricing core, including vanilla options, Black-Scholes model, Greeks calculation
- **swap.py**: Interest rate swap pricing, including vanilla swaps, cross-currency swaps, cash flow analysis
- **forward.py**: Forward pricing, including forward exchange rates, forward rate calculations
- **curve.py**: Yield curve construction and interpolation, including forward rates, zero rate calculations
- **volatility.py**: Volatility models, including Heston model, local volatility models

### 2. Auxiliary Function Modules
- **mcp_calendar.py**: Calendar tools, handling trading calendars and date calculations
- **mcp_server_mktdata.py**: Market data acquisition and processing
- **server_factory.py**: Server factory, providing new APIs with _Svr suffix
- **xscript.py**: Script execution functionality
- **quick_method.py**: Quick calculation methods

### 3. Utility Function Modules
- **utils.py**: General utility functions, including string processing, array operations, mathematical calculations

## Code Standards

### 1. Import Standards
- All modules use unified import order: Standard Library → Third Party Libraries → Local Modules
- Use explicit import statements, avoid `from module import *`
- Add type hint support

### 2. Function Comments
- Every function has complete docstring
- Includes parameter descriptions, return value descriptions, functionality descriptions
- Use English comments for better understanding

### 3. Code Style
- Unified code formatting and indentation
- Clear function grouping and comment separation
- Consistent naming conventions

## Usage Instructions

### 1. Excel Function Calls
All functions can be called directly in Excel, with function names and parameters remaining unchanged to ensure backward compatibility.

### 2. Module Import
When importing modules in Python code, use relative paths:
```python
from pyxll_func.core import bond, option, swap
```

### 3. Server-side Functions
New server-side functions use `_Svr` suffix, for example:
- `McpFixedRateBond_Svr`: Server-side fixed rate bond function
- `McpVanillaSwap_Svr`: Server-side vanilla swap function

## Maintenance Guidelines

### 1. Adding New Functions
- Add functions in appropriate modules
- Add complete docstring
- Ensure function names comply with naming conventions

### 2. Modifying Existing Functions
- Keep function signatures unchanged
- Update docstring
- Ensure backward compatibility

### 3. Code Review
- Check if import statements are standardized
- Ensure all functions have comments
- Verify code format consistency
