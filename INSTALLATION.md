# MCP Installation Guide

This guide provides step-by-step instructions for installing the MCP (Mathema Calculation Plus) library on Windows systems.

## 🚀 Installation Methods

MCP supports two installation methods:

### 🎯 Quick Installation (Recommended)

**Best for**: Most users, beginners, production environments

**Advantages**:
- ✅ One-click installation
- ✅ Automatic error handling and recovery
- ✅ Comprehensive system detection
- ✅ Built-in verification and testing
- ✅ Professional installation experience

#### Quick Installation Steps
1. **Download and extract** the MCP library to your desired location
2. **Run the installation script**:
   ```cmd
   quick_install.bat
   ```
3. **Follow the on-screen prompts** and restart Excel when prompted

#### Verify Installation
After installation, verify everything works:
```cmd
python test_install.py
```

### 🔧 Manual Installation

**Best for**: Advanced users, custom configurations, troubleshooting

**Advantages**:
- ✅ Full control over installation process
- ✅ Custom configuration options
- ✅ Better understanding of system setup
- ✅ Troubleshooting capabilities

### 🤔 Which Installation Method Should I Choose?

| Scenario | Recommended Method | Reason |
|----------|-------------------|---------|
| **First-time user** | Automated Installation | Easiest and most reliable |
| **Production deployment** | Automated Installation | Consistent, tested process |
| **Multiple installations** | Automated Installation | Fast and standardized |
| **Custom Python setup** | Manual Installation | Full control over configuration |
| **Troubleshooting issues** | Manual Installation | Better understanding of problems |
| **Learning MCP internals** | Manual Installation | Educational value |
| **Corporate environment** | Manual Installation | IT policy compliance |
| **Automated installation failed** | Manual Installation | Fallback option |

## 📋 Prerequisites

### System Requirements
- **Operating System**: Windows 10/11 (64-bit recommended)
- **Python**: 3.9.x (required)
- **Excel**: Microsoft Excel 2013 or later
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 500MB free space

### Required Software
1. **Python 3.9.x**
   - Download from [python.org](https://www.python.org/downloads/)
   - Make sure to check "Add Python to PATH" during installation
   - Verify installation: `python --version`

2. **Microsoft Excel**
   - Excel 2013, 2016, 2019, or 2021
   - Both 32-bit and 64-bit versions are supported

3. **PyXLL (Optional for Excel integration)**
   - Commercial license required
   - Download from [pyxll.com](https://www.pyxll.com/)
   - Install after MCP installation

## 🔧 Manual Installation

If you prefer manual installation or automated installation fails, follow these detailed steps:

### Why Choose Manual Installation?

- **Full Control**: Complete control over every installation step
- **Customization**: Ability to customize Python paths, Excel settings, etc.
- **Learning**: Better understanding of MCP's system requirements
- **Troubleshooting**: Easier to identify and fix specific issues
- **Corporate Environment**: Compliance with IT policies and restrictions

### Manual Installation Steps

### Step 1: Install Python Dependencies

```cmd
# Navigate to MCP directory
cd C:\path\to\mcp-python

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Set PYTHONPATH

Add these paths to your system PYTHONPATH:
```
C:\path\to\mcp-python
C:\path\to\mcp-python\lib\X64
```

**Windows 10/11:**
1. Press `Win + R`, type `sysdm.cpl`, press Enter
2. Click "Environment Variables"
3. Under "User variables", find or create "PYTHONPATH"
4. Add the paths above, separated by semicolons

### Step 3: Configure Excel Integration

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

## 🧪 Verify Installation

### Test Python Library
```cmd
python -c "import mcp; print('MCP installed successfully')"
```

### Test Excel Integration
1. Open Excel
2. Go to File → Options → Add-ins
3. Check if "PyXLL" is listed and enabled
4. Try using MCP functions in Excel

### Run Example Scripts
```cmd
# Test all examples
python script\03_test_python.py

# Run specific example
python example\calendar\quickstart.py
```

## 🔄 Uninstallation

To remove MCP completely:

```cmd
# Manual uninstallation - remove PYTHONPATH entries and delete MCP directory
# No automated uninstall script is provided
```

This will:
- Remove MCP paths from PYTHONPATH
- Remove PyXLL add-in from Excel
- Remove desktop shortcuts
- Optionally delete MCP files

## ❗ Troubleshooting

### Common Issues

#### 1. Python Version Error
```
[ERROR] Python 3.9.x is required, but found 3.8.x
```
**Solution:** Install Python 3.9.x from [python.org](https://www.python.org/downloads/)

#### 2. Import Error
```
ModuleNotFoundError: No module named 'mcp'
```
**Solution:** 
- Check PYTHONPATH is set correctly
- Restart command prompt
- Verify MCP files are in the correct location

#### 3. Excel Add-in Not Loading
**Solution:**
- Check Excel version compatibility
- Verify pyxll.xll is in the correct directory
- Check Excel Add-ins settings
- Restart Excel

#### 4. PyXLL Configuration Error
**Solution:**
- Update `pyxll.cfg` with correct Python path
- Ensure PyXLL is properly licensed
- Check file permissions

### Getting Help

- **Documentation**: [help.mathema.com.cn](http://help.mathema.com.cn/latest/api/)
- **GitHub Issues**: [Report problems](https://github.com/MDTSH/mcp_excel/issues)
- **Email Support**: Contact Mathema Team

## 📁 File Structure

After installation, your MCP directory should look like this:

```
mcp-python/
├── quick_install.bat        # Main installation script
├── install_helper.py        # Python installation helper
├── requirements.txt         # Python dependencies
├── mcp/                     # Core MCP library
├── example/                 # Example scripts
├── excel/                   # Excel templates
├── lib/                     # Binary libraries
│   ├── X64/                 # 64-bit libraries
│   └── Win32/               # 32-bit libraries
└── script/                  # Utility scripts
```

## 🔐 Security Notes

- Always run installation scripts as Administrator for full functionality
- PyXLL requires a valid commercial license
- MCP binary files (.pyd) are proprietary and not redistributable
- Keep your PyXLL license key secure

## 📞 Support

For technical support or questions:

- **Documentation**: [help.mathema.com.cn](http://help.mathema.com.cn/latest/api/)
- **GitHub**: [github.com/MDTSH/mcp_excel](https://github.com/MDTSH/mcp_excel)
- **Issues**: [GitHub Issues](https://github.com/MDTSH/mcp_excel/issues)

## 📊 Installation Summary

### Quick Reference

| Method | Command | Time | Difficulty | Best For |
|--------|---------|------|------------|----------|
| **Automated** | `quick_install.bat` | 2-3 min | ⭐ | Most users |
| **Quick** | `quick_install.bat` | 1-2 min | ⭐ | Fast setup |
| **Manual** | See steps above | 10-15 min | ⭐⭐⭐ | Advanced users |
| **Verify** | `python test_install.py` | 30 sec | ⭐ | All methods |

### Post-Installation Checklist

After any installation method, verify:

- [ ] Python 3.9.x is installed and working
- [ ] MCP library can be imported: `python -c "import mcp"`
- [ ] PYTHONPATH includes MCP directories
- [ ] Excel integration works (if applicable)
- [ ] Example scripts run successfully
- [ ] PyXLL add-in loads in Excel (if applicable)

### Getting Help

- **Installation Issues**: Run `python test_install.py` for diagnostics
- **Documentation**: [help.mathema.com.cn](http://help.mathema.com.cn/latest/api/)
- **GitHub Issues**: [Report problems](https://github.com/MDTSH/mcp_excel/issues)
- **Scripts Guide**: [Installation Scripts Guide](INSTALL_SCRIPTS_README.md)

---

**⚠️ Important**: This software is provided for educational and professional use. Users are responsible for compliance with all applicable regulations and third-party license terms.
