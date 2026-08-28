# MCP Quick Start

1. Extract this package and keep the folder.
2. Run `install.bat` (or `quick_install.bat`).
3. Choose language and a listed **64-bit Python 3.9–3.13**.
4. Close Excel, then reopen it.

```cmd
install.bat
```

## Check

```cmd
python test_install.py
python -c "import mcp; print('MCP works!')"
python example\calendar\quickstart.py
```

`test_install.py` should report PASS for Python version, architecture, files, `lib/X64`, PyXLL, and `import mcp`.

## Next

- [Python guide](https://help.mathema.com.cn/latest/api/userguide_python.html)
- [Excel guide](https://help.mathema.com.cn/latest/api/userguide.html)
- Templates: `excel\zh` / `excel\en` (TC01–TC46)
- More cases: [help.mathema.com.cn](https://help.mathema.com.cn/latest/api/)

## Common issues

**No usable Python**  
Install 64-bit CPython 3.9–3.13 from [python.org](https://www.python.org/downloads/) and tick PATH.

**32-bit Excel**  
Not supported. Use 64-bit Office.

**`No module named mcp`**  
Run `python` from the MCP folder, or `sys.path` must include that folder. Do not rely on `PYTHONPATH`.

**Add-in missing**  
Close every Excel window and run `install.bat` again.

**NumPy 2.x**  
`python -m pip install "numpy>=1.19,<2"`

Full steps: [INSTALLATION.md](INSTALLATION.md)
