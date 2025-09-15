@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: Quick MCP Installation Script
:: Mathema Calculation Plus - Quick Installer

echo.
echo  ================================================================================
echo.
echo                    MMMM    MMMM  CCCCC  PPPP
echo                    M  M    M  M  C      P   P
echo                    M  M    M  M  C      PPPP
echo                    M  M    M  M  C      P
echo                    M  M    M  M  CCCCC  P
echo.
echo                    Mathema Calculation Plus
echo                    Quick Installation Script
echo.
echo  ================================================================================
echo.

:: Get current directory
set "MCP_ROOT=%~dp0"
set "MCP_ROOT=%MCP_ROOT:~0,-1%"

echo [INFO] MCP Installation Directory: %MCP_ROOT%
echo.

:: Check if running as administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Not running as administrator. Some features may not work properly.
    echo [INFO] For full installation, please run as administrator.
    echo.
)

:: Run Python installation helper
echo [INFO] Running Python installation helper...
python "%MCP_ROOT%\install_helper.py"
if %errorlevel% neq 0 (
    echo [ERROR] Python installation helper failed
    echo [INFO] Please check Python installation and try again
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Quick installation completed!
echo.
echo [NEXT STEPS]
echo   1. Restart your command prompt or IDE
echo   2. Test with: python -c "import mcp"
echo   3. Restart Excel to load PyXLL add-in
echo   4. Check Excel Add-ins to ensure PyXLL is loaded
echo.
pause
