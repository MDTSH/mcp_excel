# MCPx (Mathema Calculation Plus) - FICC Derivatives Pricing Library

**[English](README.md)** | **[中文](README.zh-CN.md)**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9–3.13](https://img.shields.io/badge/python-3.9--3.13-blue.svg)](https://www.python.org/downloads/)
[![PyXLL](https://img.shields.io/badge/PyXLL-Required-orange.svg)](https://www.pyxll.com/)

**Release**: v1.6 (2026-08-31) · package `mcp_excel_1.6.20260831.zip` · kernel `1.6.15103`

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

#### GPU (optional)

Default is **CPU** (`MCP_RUNMODE = CPU` in `lib\X64\pyxll.cfg`). This package ships `cudart64_12.dll` and `curand64_10.dll`. GPU mode also needs a supported NVIDIA driver; it is not required for a normal install.

## 🛠️ Installation

MCP supports both **automated installation** (recommended) and **manual installation** methods.

### 🚀 Quick Installation (Recommended)

The easiest way to install MCP is using our automated installation script:

```cmd
install.bat
```

`quick_install.bat` is the same entry point.

#### Verify Installation
Use the same Python you selected for Excel:
```cmd
python test_install.py
```

The installer scans **64-bit CPython 3.9–3.13**, copies the matching `lib\X64\pyxll\py3xx\pyxll.xll` over `lib\X64\pyxll.xll`, writes `lib\X64\pyxll.cfg`, and registers the add-in. It does **not** set `PYTHONPATH`. 32-bit Excel is not supported. This package ships PyXLL **5.12.4** (one 64-bit xll per Python 3.9–3.13).

**📖 Detailed Installation Guide:** [INSTALLATION.md](INSTALLATION.md) · [Scripts](INSTALL_SCRIPTS_README.md)

### 🔧 Manual Installation

If you prefer manual installation or automated installation fails:

#### Prerequisites
- **Python**: 64-bit CPython 3.9–3.13
- **OS**: Windows 10/11 64-bit
- **Excel**: 64-bit Microsoft Excel 2016 or later
- **PyXLL**: license for production (trial works for evaluation)

#### Step 1: Install Python Dependencies
```bash
cd C:\path\to\mcp_excel
C:\Path\To\Python\python.exe -m pip install -r requirements.txt
```

#### Step 2: Configure Excel Integration
1. Set `executable` in `lib\X64\pyxll.cfg` to that Python’s `pythonw.exe`.
2. Paste the PyXLL key under `[LICENSE]`, or leave empty for trial.
3. Register `lib\X64\pyxll.xll` (the installer does this), then restart Excel.

Do not set a user `PYTHONPATH`. `import mcp` loads `lib\X64\_mcp.cp3xx-win_amd64.pyd` for the current interpreter.

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
mcp_excel/
├── mcp/                          # Core MCP library
├── lib/X64/                      # Tagged _mcp.cp3xx pyds, CUDA runtime, pyxll.xll
│   └── pyxll/py39 … py313/       # PyXLL 5.12.4 add-in per CPython ABI
├── example/
├── pyxll_func/                   # Excel UDFs
└── excel/                        # Templates TC01–TC46
    ├── en/
    └── zh/


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
- **OS**: Windows 10/11 64-bit
- **Python**: 64-bit CPython 3.9–3.13
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 500MB free space (binaries are larger with five ABI pyds)
- **Excel**: 64-bit Microsoft Excel 2016 or later

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
1. **PyXLL License**: [pyxll.com](https://www.pyxll.com/) (or trial)
2. **PyXLL Module**: Bundled under `pyxll/` (no pip install)
3. **Register**: run `install.bat`, or:
   ```bash
   python -m pyxll install --install-first --non-interactive lib/X64
   python -m pyxll activate --non-interactive lib/X64
   ```

### Installation Scripts
- **install.bat** / **quick_install.bat**: one-click installer
- **install_mcp_excel.py**: installer logic
- **test_install.py**: installation check

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

- **GitHub Issues**: [Report bugs and request features](https://github.com/MDTSH/mcp_excel/issues)
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

**No matching Python / wrong ABI**
- Install 64-bit CPython 3.9–3.13 from [python.org](https://www.python.org/downloads/)
- Excel must use the same version as a shipped `_mcp.cp3xx-win_amd64.pyd`

**"ModuleNotFoundError: No module named 'mcp'"**
- `sys.path` must include the MCP root (run from that folder, or let PyXLL `pythonpath` in `pyxll.cfg` do it)
- Do not depend on a user `PYTHONPATH`
- Run `python test_install.py` with the Excel Python

**Excel add-in not loading**
- Close all Excel windows and run `install.bat` again
- Confirm 64-bit Excel and `lib\X64\pyxll.cfg` `executable`

### Get Help

- **Run diagnostics**: `python test_install.py`
- **Full guide**: [INSTALLATION.md](INSTALLATION.md)
- **Scripts guide**: [INSTALL_SCRIPTS_README.md](INSTALL_SCRIPTS_README.md)
- **GitHub issues**: [Report problems](https://github.com/MDTSH/mcp_excel/issues)

---

**⚠️ Disclaimer**: This software is provided for educational and professional use. Users are responsible for compliance with all applicable regulations and third-party license terms. The authors are not liable for any financial losses or regulatory violations.
