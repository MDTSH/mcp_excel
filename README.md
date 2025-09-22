# MCP (Mathema Calculation Platform) - FICC Derivatives Pricing Library

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PyXLL](https://img.shields.io/badge/PyXLL-Required-orange.svg)](https://www.pyxll.com/)

A comprehensive Python library for **Fixed Income, Currency, and Commodities (FICC)** derivatives pricing and risk management. MCP provides professional-grade tools for financial institutions, trading desks, and quantitative analysts, with **seamless Excel integration** that allows users to create complex financial models and templates directly within Excel spreadsheets.

## 🚀 Key Features

- **Comprehensive FICC Coverage**: Support for FX, Interest Rate, Bond, and Volatility products
- **Professional Pricing Models**: Black-Scholes, Heston, Bachelier, and advanced volatility models
- **Real-time & Historical Data**: Integration with market data providers
- **Excel Integration**: Seamless Excel add-in functionality via PyXLL
- **High Performance**: Optimized C++ core with Python wrapper
- **Production Ready**: Used by major financial institutions

## 📊 Supported Financial Products

### 💱 FX, Commodities & Equity Index Options
- **Vanilla Options**
  - Call/Put Options
  - American Style Options
  - Asian Options (Average rate/strike)
- **Exotic Options**
  - Barrier Options (Knock-in, Knock-out)
  - Touch Options (One-Touch, No-Touch)
  - Digital Options (Cash/Asset-or-Nothing)

### 🔄 Structured FX & Precious Metals Products
- **Forward Products**
  - Outright Forward
  - Range Forward (Spread Forward)
  - Floor Forward (Protected Forward)
  - Cap Forward (Capped Forward)
  - Cap & Floor Forward (Cylinder)
  - Ratio Forward
  - Dual Currency Forward
  - Target Forward

### 🏦 Interest Rate Products
- **Bonds**
  - Bullet Bonds (One-time maturity payment)
  - Callable Bonds (Embedded options)
  - Coupon Bonds (Regular interest payments)
  - Perpetual Bonds
  - Floating Rate Notes (FRN)
- **Interest Rate Swaps**
  - Standard IRS (FR007, SOFR, etc.)
  - Float/Float Swaps
  - Float/Fixed Swaps
  - Fixed/Float Swaps
- **Interest Rate Derivatives**
  - Bond Forwards
  - Bond Options
  - Swaptions (Interest Rate Swap Options)
  - Caps & Floors
  - Forward Rate Agreements (FRA)

### 📈 Market Data & Curves
- **Curve Models**
  - Forward Curves
  - Yield Curves
  - Volatility Surfaces
  - Local Volatility Models
- **Interest Rate Curves**
  - Deposit Curves
  - Bond Curves
  - Swap Curves
  - Parametric Curves
- **Interest Rate Surfaces**
  - Cap/Floor Volatility Surfaces
  - IRO Volatility Cubes

### 🏗️ Structured Products (OTC Derivatives or Structued Deposit)
Customized structured options linked to interest rates, FX rates, commodities, and equity indices:

- **Double No Touch** (Bilateral barrier)
- **Triple Ranges Put** (Three-level put structure)
- **Range Accrual** (Accumulative range)
- **Digital Call** (Binary call option)
- **Autocallables** (Monthly observation auto-call)
- **Triple Ranges Call** (Three-level call structure)
- **Cash Delivery Forward** (Subsidized delivery structured forward)
- **Double Ranges** (Dual-level structure)
- **Digital Put** (Binary put option)
- **Single Touch** (One-sided barrier)
- **Call Put Spread** (Spread structure)
- **Auto Call** (Callable structure)
- **Shark Fin** (Dual shark fin)
- **Dual Shark Fin** (Bidirectional shark fin)
- **Discrete Double No Touch** (Daily observation EUR/USD)
- **Discrete One Touch Downside** (Downward one-touch)
- **Discrete One Touch Upside** (Upward one-touch)
- **Discrete Ping Pong Option** (Discrete ping-pong option)
- **Single Range Accrual Call** (One-sided call range accrual)
- **Single Range Accrual Put** (One-sided put range accrual)
- **Custom Structures** (More tailored products available)

#### 🚀 GPU Acceleration Support
Structured products utilize Monte Carlo simulation and support **GPU acceleration** for enhanced performance. If your machine has NVIDIA RTX series or compatible GPUs installed, you can enable GPU acceleration through:

1. **PyXLL Configuration**: Set `MCP_RUNMODE = GPU` in `pyxll.cfg`
2. **Environment Variable**: Set `MCP_RUNMODE = GPU` in system environment variables

GPU acceleration significantly improves calculation speed for complex structured products pricing.

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

2. **Determine Excel Version:**
   - Open Excel
   - Go to **File** → **Account** → **About Excel**
   - Check if it shows "Microsoft Excel 2016 (64-bit)" or "Microsoft Excel 2016 (32-bit)"
   - Or press **Ctrl + G**, type `=INFO("numfile")`, press Enter
   - If the result is 1, you have 32-bit Excel; if it's 2, you have 64-bit Excel

3. **Install PyXLL add-in:**
   - Based on your Excel version, choose the correct file:
     - **64-bit Excel**: Use `lib\X64\pyxll.xll`
     - **32-bit Excel**: Use `lib\Win32\pyxll.xll`
   - Go to **File** → **Options** → **Add-ins**
   - At the bottom, select **Excel Add-ins** from the dropdown and click **Go**
   - Click **Browse** and navigate to the correct `pyxll.xll` file
   - Select the file and click **OK**
   - Ensure the add-in is checked and click **OK**

4. **Restart Excel** and verify the add-in is loaded

#### Step 4: Verify Installation
```cmd
# Test Python library
python -c "import mcp; print('MCP installed successfully')"

# Test example
python example\calendar\quickstart.py
```

**📖 Detailed Manual Installation Guide:** [Manual Installation Guide](INSTALLATION.md)

**📖 Python API Guide:** [Python User Guide](http://help.mathema.com.cn/latest/api/userguide_python.html)

**📖 Excel API Guide:** [Excel User Guide](http://help.mathema.com.cn/latest/api/userguide.html)


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
├── mcp/                          # Core MCP library python files
│   ├── tool/                     # Main pricing tools
│   ├── utils/                    # Utilities and enums
│   ├── forward/                  # Forward pricing
│   └── server_version/           # Server-side APIs
├── lib/                          # Core MCP library pyd files
│   ├── Win32/                    # Win32 pyd files
│   ├── X64/                      # X64 pyd files
├── example/                      # Pytho Example scripts
│   ├── calendar/                 # Calendar examples
│   ├── fixedincome/              # Fixed income examples
│   ├── forward_curve/            # Forward curve examples
│   ├── option/                   # Option pricing examples
│   ├── volsurface2/              # Volatility surface examples
│   └── yield_curve/              # Yield curve examples
├── pyxll_func/                   # Excel add-in pyxll functions
│   ├── core/                     # Core MCP functions
│   └── custom/                   # Any customzation functions be here!
└── excel/                        # Excel templates and examples
    ├── en/                       # English Version excel and docs
    └── zh/                       # Chinese Version excel and docs


```

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
- **Python Examples**: See the `example/` directory for comprehensive examples
- **Excel Examples**: See the `excel/` directory for comprehensive excel template
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
   - **Enhanced way**: Run `python register_pyxll.py`
   - **Manual way**: 
     ```bash
     python -m pyxll install --install-first --non-interactive lib/X64
     python -m pyxll activate --non-interactive lib/X64
     ```

### Installation Scripts
- **quick_install.bat**: Main automated installation script
- **install_helper.py**: Python installation helper (included in quick_install.bat)
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

## ❗ Troubleshooting

### Common Issues

**"Python 3.9.x required"**
- Install Python 3.9.x from [python.org](https://www.python.org/downloads/)

**"ModuleNotFoundError: No module named 'mcp'"**
- Check PYTHONPATH is set correctly
- Restart command prompt
- Run `python test_install.py` for diagnostics

**Excel add-in not loading**
- Restart Excel
- Check Excel Add-ins settings
- Verify PyXLL is installed

**Windows 11 Specific Issues**

If you're using Windows 11 and encounter these errors:
- `ModuleNotFoundError: No module named 'mcp._mcp'`
- Excel shows "Error importing Python modules"

**Solution**: Copy and rename DLL files from system directory:

1. Navigate to `C:\Windows\system32\`
2. Find these files:
   - `msvcr120_clr0400.dll`
   - `msvcp120_clr0400.dll`
3. Copy them to `.\lib\X64\` and rename to:
   - `msvcr120.dll`
   - `msvcp120.dll`

**Note**: Why this works? We don't know either 😅 - but it fixes the issue on Windows 11!

### Get Help

- **Run diagnostics**: `python test_install.py`
- **Full guide**: [INSTALLATION.md](INSTALLATION.md)
- **Scripts guide**: [INSTALL_SCRIPTS_README.md](INSTALL_SCRIPTS_README.md)
- **GitHub issues**: [Report problems](https://github.com/MDTSH/mcp_excel/issues)

---

**⚠️ Disclaimer**: This software is provided for educational and professional use. Users are responsible for compliance with all applicable regulations and third-party license terms. The authors are not liable for any financial losses or regulatory violations.
