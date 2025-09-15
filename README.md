# MCP (Mathema Calculation Platform) - FICC Derivatives Pricing Library

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PyXLL](https://img.shields.io/badge/PyXLL-Required-orange.svg)](https://www.pyxll.com/)

A comprehensive Python library for **Fixed Income, Currency, and Commodities (FICC)** derivatives pricing and risk management. MCP provides professional-grade tools for financial institutions, trading desks, and quantitative analysts.

## 🚀 Key Features

- **Comprehensive FICC Coverage**: Support for FX, Interest Rate, Bond, and Volatility products
- **Professional Pricing Models**: Black-Scholes, Heston, Bachelier, and advanced volatility models
- **Real-time & Historical Data**: Integration with market data providers
- **Excel Integration**: Seamless Excel add-in functionality via PyXLL
- **High Performance**: Optimized C++ core with Python wrapper
- **Production Ready**: Used by major financial institutions

## 📊 Supported Financial Products

### 🏦 Interest Rate Products
- **Vanilla Interest Rate Swaps** (IRS)
- **Cross-Currency Swaps** (CCS)
- **Swaptions** (Black-76, Bachelier models)
- **Caps & Floors** with volatility stripping
- **Overnight Rate Swaps** (SOFR, ESTR, etc.)
- **Bond Futures** and **Bill Futures**

### 💱 Foreign Exchange Products
- **FX Vanilla Options** (European, American)
- **FX Digital Options** (Cash/Asset-or-Nothing)
- **FX Barrier Options** (Knock-in, Knock-out)
- **FX Asian Options** (Average rate/strike)
- **FX Forward Contracts**
- **FX Structured Products** (Autocallable, etc.)

### 📈 Volatility Products
- **FX Volatility Surfaces** (Bilateral support)
- **Interest Rate Volatility Surfaces**
- **Local Volatility Models** (Dupire, Heston)
- **Historical Volatility Analysis**
- **Volatility Smile Interpolation**

### 🏛️ Fixed Income Products
- **Fixed Rate Bonds** (Government, Corporate)
- **Floating Rate Notes** (FRN)
- **Zero-Coupon Bonds**
- **Bond Futures** and **Bill Futures**
- **Bond Options** and **Embedded Options**

### 📊 Market Data & Curves
- **Yield Curves** (Single-sided, Bilateral)
- **Forward Rate Curves**
- **FX Forward Points Curves**
- **Swap Curves** (Multiple currencies)
- **Bond Curves** and **Deposit Curves**
- **Cross-Currency Basis Curves**

## 🛠️ Installation

MCP supports both **automated installation** (recommended) and **manual installation** methods.

### 🚀 Quick Installation (Recommended)

The easiest way to install MCP is using our automated installation script:

```cmd
# Download and extract MCP to your desired location
# Then run the installation script
quick_install.bat
```

#### Verify Installation
After installation, verify everything works:
```cmd
python test_install.py
```

**Features of Quick Installation:**
- ✅ Automatic Python 3.9.x compatibility check
- ✅ Automatic dependency installation
- ✅ System architecture detection (x64/Win32)
- ✅ Excel version detection and configuration
- ✅ PYTHONPATH environment setup
- ✅ PyXLL Excel add-in installation (optional)
- ✅ Comprehensive error handling and recovery

**📖 Detailed Installation Guide:** [Installation Scripts Guide](INSTALL_SCRIPTS_README.md)

### 🔧 Manual Installation

If you prefer manual installation or automated installation fails:

#### Prerequisites
- **Python**: 3.9.x (required)
- **OS**: Windows 10/11 (64-bit recommended)
- **Excel**: Microsoft Excel 2016 or later
- **PyXLL**: Professional License (for Excel integration)

#### Step 1: Install Python Dependencies
```bash
# Navigate to MCP directory
cd C:\path\to\mcp-python

# Install dependencies
pip install -r requirements.txt
```

#### Step 2: Set PYTHONPATH Environment Variable
Add these paths to your system PYTHONPATH:
```
C:\path\to\mcp-python
C:\path\to\mcp-python\lib\X64
```

**Windows 10/11 Setup:**
1. Press `Win + R`, type `sysdm.cpl`, press Enter
2. Click "Environment Variables"
3. Under "User variables", find or create "PYTHONPATH"
4. Add the paths above, separated by semicolons

#### Step 3: Configure Excel Integration
1. **Update pyxll.cfg:**
   - Open `lib\X64\pyxll.cfg` (or `lib\Win32\pyxll.cfg` for 32-bit)
   - Update the `executable` line to point to your Python installation:
     ```
     executable = C:\Python39\python.exe
     ```

2. **Install PyXLL add-in:**
   - Copy `lib\X64\pyxll.xll` to your Excel startup directory
   - Common locations:
     - `%APPDATA%\Microsoft\Excel\XLSTART\`
     - `%APPDATA%\Microsoft\AddIns\`

3. **Restart Excel** and check Add-ins

#### Step 4: Verify Installation
```cmd
# Test Python library
python -c "import mcp; print('MCP installed successfully')"

# Test all examples
python script\03_test_python.py
```

**📖 Detailed Manual Installation Guide:** [Manual Installation Guide](INSTALLATION.md)

**📖 Python API Guide:** [Python User Guide](http://help.mathema.com.cn/latest/api/userguide_python.html)

**📖 Excel API Guide:** [Excel User Guide](http://help.mathema.com.cn/latest/api/userguide.html)

### 📊 Installation Methods Comparison

| Feature | Automated Installation | Manual Installation |
|---------|----------------------|-------------------|
| **Ease of Use** | ⭐⭐⭐⭐⭐ One-click setup | ⭐⭐ Requires technical knowledge |
| **Speed** | ⭐⭐⭐⭐⭐ Fast (2-3 minutes) | ⭐⭐ Slower (10-15 minutes) |
| **Error Handling** | ⭐⭐⭐⭐⭐ Comprehensive | ⭐ Manual troubleshooting |
| **Excel Integration** | ⭐⭐⭐⭐⭐ Automatic | ⭐⭐ Manual configuration |
| **PYTHONPATH Setup** | ⭐⭐⭐⭐⭐ Automatic | ⭐ Manual environment setup |
| **Dependency Management** | ⭐⭐⭐⭐⭐ Automatic | ⭐⭐ Manual pip install |
| **System Detection** | ⭐⭐⭐⭐⭐ Automatic | ⭐ Manual verification |
| **Recovery Options** | ⭐⭐⭐⭐⭐ Built-in rollback | ⭐ Manual cleanup |
| **Customization** | ⭐⭐⭐ Limited options | ⭐⭐⭐⭐⭐ Full control |
| **Troubleshooting** | ⭐⭐⭐⭐ Detailed logs | ⭐ Manual debugging |

**Recommendation**: Use **Automated Installation** for most users, **Manual Installation** only if you need specific customization or automated installation fails.

**🚀 New to MCP?** Check out our [Quick Start Guide](QUICK_START.md) for a 5-minute setup!

## 💡 Quick Examples

### FX Vanilla Option Pricing

```python
from mcp.tool.tools_main import McpVanillaOption
from mcp.utils.enums import BuySell, CallPut, OptionExpiryNature

# Create option parameters
option_args = {
    'Pair': 'USD/CNY',
    'BuySell': BuySell.Buy,
    'CallPut': CallPut.Call,
    'OptionExpiryNature': OptionExpiryNature.EUROPEAN,
    'StrikePx': 7.3,
    'SpotPx': 7.0671,
    'Volatility': 0.0484,
    'DomesticRate': 0.0186,
    'ForeignRate': 0.0475,
    'ExpiryDate': '2025-02-14',
    'DeliveryDate': '2025-02-18',
    'FaceAmount': 1000000
}

# Price the option
option = McpVanillaOption(option_args)
price = option.Price()
print(f"Option Price: {price:.2f}")
```

### Yield Curve Construction

```python
from mcp.tool.tools_main import McpYieldCurve2
from mcp.utils.enums import DayCounter, Frequency

# Build bilateral yield curve
curve_args = {
    'ReferenceDate': '2024-12-13',
    'Tenors': ['ON', '1M', '3M', '6M', '1Y', '2Y', '5Y'],
    'BidZeroRates': [0.0458, 0.0433, 0.0433, 0.0433, 0.0433, 0.043, 0.042],
    'AskZeroRates': [0.0459, 0.0458, 0.0458, 0.0458, 0.0458, 0.046, 0.045],
    'DayCounter': DayCounter.Act365Fixed,
    'Frequency': Frequency.Continuous
}

curve = McpYieldCurve2(curve_args)
zero_rate = curve.ZeroRate('2025-12-13', 'mid')
print(f"1Y Zero Rate: {zero_rate*100:.4f}%")
```

### FX Forward Points Curve

```python
from mcp.tool.tools_main import McpFXForwardPointsCurve2

# Build bilateral forward points curve
forward_args = {
    'ReferenceDate': '2024-12-13',
    'Pair': 'USD/CNY',
    'FXSpotRate': 7.1650,
    'Tenors': ['ON', '1M', '3M', '6M', '1Y'],
    'BidForwardPoints': [-22.0, -250, -733, -1393, -2395],
    'AskForwardPoints': [-21.0, -248, -730, -1390, -2390]
}

forward_curve = McpFXForwardPointsCurve2(forward_args)
points = forward_curve.FXForwardPoints('2025-03-13', 'mid')
print(f"3M Forward Points: {points:.1f}")
```

## 📁 Project Structure

```
mcp-python/
├── mcp/                          # Core MCP library
│   ├── tool/                     # Main pricing tools
│   ├── utils/                    # Utilities and enums
│   ├── forward/                  # Forward pricing
│   └── server_version/           # Server-side APIs
├── example/                      # Example scripts
│   ├── calendar/                 # Calendar examples
│   ├── fixedincome/              # Fixed income examples
│   ├── forward_curve/            # Forward curve examples
│   ├── option/                   # Option pricing examples
│   ├── volsurface2/              # Volatility surface examples
│   └── yield_curve/              # Yield curve examples
├── excel/                        # Excel templates and examples
└── pyxll_func/                   # Excel add-in functions

```

## 🧪 Testing

Run the comprehensive test suite:

```bash
python script/03_test_python.py
```

This will test all example scripts and verify functionality.

## 📚 Documentation

### Getting Started
- **🚀 Quick Start**: [5-minute setup guide](QUICK_START.md)
- **📖 Installation Guide**: [Complete installation instructions](INSTALLATION.md)
- **🔧 Scripts Guide**: [Installation scripts documentation](INSTALL_SCRIPTS_README.md)

### API Documentation
- **API Reference**: [help.mathema.com.cn](http://help.mathema.com.cn/latest/api/)
- **Python Guide**: [Python User Guide](http://help.mathema.com.cn/latest/api/userguide_python.html)
- **Excel Guide**: [Excel User Guide](http://help.mathema.com.cn/latest/api/userguide.html)

### Examples and Learning
- **Examples**: See the `example/` directory for comprehensive examples
- **Contributing**: [How to contribute](CONTRIBUTING.md)
- **License**: [MIT License details](LICENSE)

## 🔧 Requirements

### System Requirements
- **OS**: Windows 10/11 (64-bit recommended)
- **Python**: 3.9.x (required)
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 500MB free space
- **Excel**: Microsoft Excel 2016 or later (for Excel integration)

### Dependencies

#### Essential Dependencies (Automatically Installed)
- **NumPy**: Numerical computing
- **Pandas**: Data manipulation  
- **Requests**: HTTP requests for server functions
- **Python-dateutil**: Date handling

#### Optional Dependencies
- **PyXLL**: Commercial license required for Excel integration
- **Matplotlib**: Plotting and visualization
- **Jupyter**: Notebook support
- **Development tools**: pytest, black, flake8, mypy

To install optional dependencies:
```bash
pip install -r requirements-optional.txt
```

#### Excel Integration (PyXLL)
MCP includes PyXLL module for Excel integration:
1. **PyXLL License**: Purchase from [pyxll.com](https://www.pyxll.com/)
2. **PyXLL Module**: Already included in MCP (no pip install needed)
3. **Register MCP Add-in**: 
   - **Easy way**: Run `install_pyxll.bat`
   - **Enhanced way**: Run `python register_pyxll.py`
   - **Manual way**: 
     ```bash
     python -m pyxll install --install-first --non-interactive lib/X64
     python -m pyxll activate --non-interactive lib/X64
     ```

### Installation Scripts
- **quick_install.bat**: Main automated installation script
- **uninstall_mcp.bat**: Complete removal script
- **install_helper.py**: Python installation helper
- **test_install.py**: Installation verification script

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

**Important Notes:**
- Python source code is open source and freely distributable
- Compiled binary components (.pyd files) are proprietary
- PyXLL requires a separate commercial license
- Excel templates are freely usable under MIT License

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 🆘 Support

- **GitHub Issues**: [Report bugs and request features](https://github.com/MDTSH/mcp-python/issues)
- **Documentation**: [help.mathema.com.cn](http://help.mathema.com.cn/latest/api/)
- **Community**: Join our discussions for help and best practices

## 🏢 About Mathema Team

Mathema Team specializes in quantitative finance and derivatives pricing solutions. Our MCP platform is used by leading financial institutions worldwide for:

- Risk management and compliance
- Trading desk operations
- Quantitative research
- Regulatory reporting
- Portfolio valuation

## 🔗 Links

- **Website**: [mathema.com.cn](https://mathema.com.cn)
- **Documentation**: [help.mathema.com.cn](http://help.mathema.com.cn/latest/api/)
- **PyXLL**: [www.pyxll.com](https://www.pyxll.com/)
- **GitHub**: [github.com/MDTSH](https://github.com/MDTSH)

---

**⚠️ Disclaimer**: This software is provided for educational and professional use. Users are responsible for compliance with all applicable regulations and third-party license terms. The authors are not liable for any financial losses or regulatory violations.
