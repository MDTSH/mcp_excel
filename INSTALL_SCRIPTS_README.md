# MCP Installation Scripts

## Scripts

| File | Role |
|------|------|
| `install.bat` | Entry point. Starts `install_mcp_excel.py` via `py -3` or `python`. |
| `quick_install.bat` | Same as `install.bat` (forwards all arguments). |
| `install_mcp_excel.py` | Installer (stdlib only). Any Python 3.8+ can run it. |
| `test_install.py` | Checks 64-bit CPython 3.9–13, tagged pyds, `import mcp`. |

## What the installer does

1. Language: Chinese (default) or English (`--lang zh|en`).
2. Scan 64-bit CPython 3.9–3.13 that have a matching `_mcp.cp3xx-win_amd64.pyd`.
3. Prefer an interpreter that already has numpy 1.x / pandas / requests / dateutil.
4. Patch `lib\X64\pyxll.cfg` `executable` (prefer `pythonw.exe`) and license. Backup first.
5. Does **not** set `PYTHONPATH`.
6. Register `lib\X64\pyxll.xll` unless `--skip-excel`.

32-bit Excel is rejected unless `--skip-excel`.

## Usage

```cmd
install.bat
install.bat --lang en
install.bat --probe-only
install.bat --skip-excel
install.bat --python C:\Path\To\python.exe
install.bat --install-deps
```

Log: `logs\mcp_install.log` (license values in argv are redacted).

## Verify

```cmd
python test_install.py
```

Use the Python you chose for Excel.

## Uninstall

Uncheck PyXLL in Excel Add-ins, then delete the MCP folder.

Help: [help.mathema.com.cn](https://help.mathema.com.cn/latest/api/) · [GitHub Issues](https://github.com/MDTSH/mcp_excel/issues)
