# MCP Installation Scripts

This document describes the automated installation scripts for the MCP (Mathema Calculation Plus) library.

## 📁 Available Scripts

### 1. `quick_install.bat` - Main Installation Script
**Purpose**: Complete automated installation with comprehensive functionality

**Features**:
- ✅ Displays MCP logo and branding
- ✅ Checks Python 3.9.x compatibility
- ✅ Installs Python dependencies from requirements.txt
- ✅ Detects system architecture (x64/Win32)
- ✅ Finds Excel installations and versions
- ✅ Sets up PYTHONPATH environment variable
- ✅ Configures PyXLL for Excel integration (optional)
- ✅ Installs PyXLL add-in to Excel (optional)
- ✅ Comprehensive error handling and recovery
- ✅ Provides detailed installation summary

**Usage**:
```cmd
quick_install.bat
```

### 3. Manual Uninstallation
**Purpose**: Complete removal of MCP installation

**Manual Steps**:
- Remove MCP paths from PYTHONPATH environment variable
- Remove PyXLL add-in from Excel Add-ins
- Delete MCP installation directory
- Clean up temporary files if any

**Note**: No automated uninstall script is provided. Follow manual removal steps as needed.

### 4. `install_helper.py` - Python Installation Helper
**Purpose**: Python-based installation logic with advanced features

**Features**:
- ✅ Cross-platform Python logic
- ✅ Excel version detection
- ✅ PyXLL configuration management
- ✅ PYTHONPATH management
- ✅ Dependency installation
- ✅ MCP import testing

**Usage**:
```cmd
python install_helper.py
```

### 5. `test_install.py` - Installation Verification
**Purpose**: Test and verify installation status

**Features**:
- ✅ Python version compatibility check
- ✅ System architecture detection
- ✅ File structure validation
- ✅ PYTHONPATH verification
- ✅ MCP import testing
- ✅ Detailed test report

**Usage**:
```cmd
python test_install.py
```

## 🚀 Installation Process

### Automated Installation (Recommended)

1. **Download** MCP library to your system
2. **Run as Administrator**:
   ```cmd
   quick_install.bat
   ```
3. **Follow prompts** and restart Excel when complete

### Quick Installation

For faster installation:
```cmd
quick_install.bat
```

### Verification

After installation, verify everything works:
```cmd
python test_install.py
```

## 🔧 Script Features

### Error Handling
- ✅ Comprehensive error checking
- ✅ Graceful failure handling
- ✅ Detailed error messages
- ✅ Recovery suggestions

### User Experience
- ✅ Clear progress indicators
- ✅ Color-coded status messages
- ✅ Professional branding
- ✅ Step-by-step guidance

### System Compatibility
- ✅ Windows 10/11 support
- ✅ 32-bit and 64-bit architecture
- ✅ Multiple Excel versions
- ✅ Python 3.9.x requirement

### Safety Features
- ✅ Backup creation before changes
- ✅ Confirmation prompts
- ✅ Rollback capabilities
- ✅ Non-destructive testing

## 📋 Prerequisites

### System Requirements
- **OS**: Windows 10/11 (64-bit recommended)
- **Python**: 3.9.x (required)
- **Excel**: 2013 or later
- **Memory**: 4GB RAM minimum
- **Storage**: 500MB free space

### Required Software
1. **Python 3.9.x** from [python.org](https://www.python.org/downloads/)
2. **Microsoft Excel** 2013 or later
3. **PyXLL** (optional, for Excel integration)

## 🛠️ Manual Configuration

If automated installation fails, you can configure manually:

### PYTHONPATH Setup
Add these paths to your system PYTHONPATH:
```
C:\path\to\mcp-python
C:\path\to\mcp-python\lib\X64
```

### Excel Integration
1. Update `lib\X64\pyxll.cfg` with your Python path
2. Copy `lib\X64\pyxll.xll` to Excel startup directory
3. Restart Excel

## ❗ Troubleshooting

### Common Issues

#### Python Version Error
```
[ERROR] Python 3.9.x is required, but found 3.8.x
```
**Solution**: Install Python 3.9.x

#### Import Error
```
ModuleNotFoundError: No module named 'mcp'
```
**Solution**: Check PYTHONPATH and restart command prompt

#### Excel Add-in Not Loading
**Solution**: 
- Verify pyxll.xll is in correct directory
- Check Excel Add-ins settings
- Restart Excel

### Getting Help
- **Documentation**: [help.mathema.com.cn](http://help.mathema.com.cn/latest/api/)
- **GitHub Issues**: [Report problems](https://github.com/MDTSH/mcp_excel/issues)

## 📊 Installation Status

After running `test_install.py`, you should see:
```
Test Summary:
  Python Version: PASS
  System Architecture: PASS
  MCP Files: PASS
  Library Directories: PASS
  PYTHONPATH: PASS
  MCP Import: PASS

Overall: 6/6 tests passed
✓ All tests passed! MCP is ready to use.
```

## 🔄 Uninstallation

To completely remove MCP:
1. Remove MCP paths from PYTHONPATH environment variable
2. Remove PyXLL add-in from Excel
3. Delete MCP installation directory manually

This will:
- Remove all MCP paths from PYTHONPATH
- Remove PyXLL add-in from Excel
- Remove desktop shortcuts
- Optionally delete MCP files

## 📞 Support

For technical support:
- **Documentation**: [help.mathema.com.cn](http://help.mathema.com.cn/latest/api/)
- **GitHub**: [github.com/MDTSH/mcp_excel](https://github.com/MDTSH/mcp_excel)
- **Issues**: [GitHub Issues](https://github.com/MDTSH/mcp_excel/issues)

---

**⚠️ Important**: Always run installation scripts as Administrator for full functionality. PyXLL requires a valid commercial license for Excel integration.
