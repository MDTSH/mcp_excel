# MCP Quick Start Guide

Get MCP (Mathema Calculation Plus) up and running in minutes!

## 🚀 One-Click Installation

### For Most Users (Recommended)

1. **Download** MCP to your computer
2. **Run** `quick_install.bat`
3. **Follow prompts** and restart Excel when done
4. **Done!** MCP is ready to use

```cmd
# That's it! Just run this:
quick_install.bat
```

### For Advanced Users

If you need more control or automated installation fails:

```cmd
# Manual installation steps:
pip install -r requirements.txt
# Set PYTHONPATH environment variable
# Configure Excel integration
# See INSTALLATION.md for details
```

## ✅ Verify Installation

After installation, test that everything works:

```cmd
python test_install.py
```

You should see:
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

## 🧪 Test MCP

Try a quick test:

```python
# Test Python library
python -c "import mcp; print('MCP works!')"

# Run examples
python example\calendar\quickstart.py
```

## 📚 Next Steps

- **Learn MCP**: [Python Guide](http://help.mathema.com.cn/latest/api/userguide_python.html)
- **Excel Integration**: [Excel Guide](http://help.mathema.com.cn/latest/api/userguide.html)
- **Examples**: Check the `example/` directory
- **Full Documentation**: [help.mathema.com.cn](http://help.mathema.com.cn/latest/api/)

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


**Ready to start?** Run `quick_install.bat` and you'll be using MCP in minutes! 🚀
