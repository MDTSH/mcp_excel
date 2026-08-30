@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
cd /d "%~dp0"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

where py >nul 2>&1
if !errorlevel! == 0 (
    py -3 -c "import sys" >nul 2>&1
    if !errorlevel! == 0 (
        py -3 "%~dp0install_mcp_excel.py" %*
        exit /b !errorlevel!
    )
)

where python >nul 2>&1
if !errorlevel! == 0 (
    python "%~dp0install_mcp_excel.py" %*
    exit /b !errorlevel!
)

echo.
echo [ERROR] No Python found. Install 64-bit Python 3.9-3.13 from
echo         https://www.python.org/downloads/
echo         and tick "Add python.exe to PATH".
echo.
echo [错误] 未找到 Python。请先安装 64 位 Python 3.9–3.13：
echo         https://www.python.org/downloads/
echo         安装时勾选 Add python.exe to PATH。
echo.
pause
exit /b 1
