# MCP Installation Guide

Windows 10/11, **64-bit Excel**, and **64-bit CPython 3.9–3.13**.

## Quick install (recommended)

1. Extract this package to a folder you will keep (do not delete it after install).
2. Double-click `install.bat` (or `quick_install.bat` — same script).
3. Choose language, pick a listed Python, paste a PyXLL license if you have one (Enter = trial).
4. Close Excel completely, then reopen it.

The installer:

- Scans 64-bit CPython 3.9–3.13 that match a shipped `_mcp.cp3xx-win_amd64.pyd` and `lib\X64\pyxll\py3xx\pyxll.xll` (PyXLL 5.12.4)
- Copies that xll over `lib\X64\pyxll.xll`, then writes `lib\X64\pyxll.cfg` (`executable` + license). It does **not** set `PYTHONPATH`
- Optionally installs `numpy` / `pandas` / `requests` / `python-dateutil` (default: skip)
- Registers `lib\X64\pyxll.xll`

Verify:

```cmd
python test_install.py
```

Run `test_install.py` with the **same** Python you selected for Excel.

## Prerequisites

- Windows 10/11 **64-bit**
- **64-bit** Microsoft Excel 2016 or later (32-bit Excel is not supported)
- **64-bit CPython 3.9, 3.10, 3.11, 3.12, or 3.13** from [python.org](https://www.python.org/downloads/) — tick “Add python.exe to PATH”
- PyXLL license for production Excel use ([pyxll.com](https://www.pyxll.com/)); trial is enough to try the add-in
- About 500 MB disk; 8 GB RAM recommended

## Manual installation

Use this only if the script cannot run.

1. Install dependencies into the Python that Excel will use:

   ```cmd
   cd C:\path\to\mcp_excel
   C:\Path\To\Python\python.exe -m pip install -r requirements.txt
   ```

   Keep NumPy on 1.x (`numpy>=1.19,<2`).

2. Edit `lib\X64\pyxll.cfg`:
   - `executable` = that Python’s `pythonw.exe` (or `python.exe`)
   - `[LICENSE] key` = your PyXLL key (or leave empty for trial)

3. Register the add-in (from the MCP folder):

   ```cmd
   C:\Path\To\Python\python.exe -m pyxll install --install-first --non-interactive lib\X64
   C:\Path\To\Python\python.exe -m pyxll activate --non-interactive lib\X64
   ```

4. Close and reopen Excel.

You do **not** need a user `PYTHONPATH`. `mcp/__init__.py` loads `lib\X64\_mcp.cp3xx-win_amd64.pyd` for the running interpreter.

## Verify

```cmd
python -c "import mcp; print('MCP OK', mcp._mcp.__file__)"
python test_install.py
python example\calendar\quickstart.py
```

In Excel: File → Options → Add-ins → confirm PyXLL is enabled.

## Uninstall

1. Excel → File → Options → Add-ins → Excel Add-ins → uncheck PyXLL.
2. Delete the MCP folder.

## Troubleshooting

**No matching Python**  
Install 64-bit CPython 3.9–3.13. This package has one `_mcp.cp3xx-win_amd64.pyd` per version.

**32-bit Excel**  
Not supported. Install 64-bit Office. `install.bat --skip-excel` only writes Python/config.

**`import mcp` fails / DLL load failed**  
Use the same ABI as the pyd (3.11 Python needs `cp311`). Keep `cudart64_12.dll` and `curand64_10.dll` next to the pyds.

**NumPy 2.x**  
Reinstall: `python -m pip install "numpy>=1.19,<2"`

**Excel add-in not loading**  
Close all Excel windows, run `install.bat` again, check `lib\X64\pyxll.cfg` `executable`.

**PyXLL license**  
Paste the key in the installer or in `[LICENSE] key`. Empty key uses the trial.

Help: [help.mathema.com.cn](https://help.mathema.com.cn/latest/api/) · [GitHub Issues](https://github.com/MDTSH/mcp_excel/issues)

## Layout

```
mcp_excel/
├── install.bat / quick_install.bat
├── install_mcp_excel.py
├── test_install.py
├── requirements.txt
├── mcp/                 # Python package (loads lib/X64 by ABI)
├── lib/X64/             # tagged pyds, CUDA runtime, pyxll.xll, pyxll.cfg
├── pyxll/               # PyXLL Python module
├── pyxll_func/          # Excel UDFs
├── example/
└── excel/zh , excel/en  # templates TC01–TC46
```

Default run mode is **CPU** (`MCP_RUNMODE = CPU` in `pyxll.cfg`). GPU needs a supported NVIDIA driver; this package ships `cudart64_12.dll` and `curand64_10.dll` only.
