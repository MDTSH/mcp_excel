@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: MCP Uninstallation Script
:: Mathema Calculation Plus - Uninstaller

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
echo                    Uninstaller Script
echo.
echo  ================================================================================
echo.

:: Get current directory
set "MCP_ROOT=%~dp0"
set "MCP_ROOT=%MCP_ROOT:~0,-1%"

echo [INFO] MCP Installation Directory: %MCP_ROOT%
echo.

:: Confirm uninstallation
set /p "CONFIRM=Are you sure you want to uninstall MCP? (y/N): "
if /i not "%CONFIRM%"=="y" (
    echo [INFO] Uninstallation cancelled.
    pause
    exit /b 0
)

echo.
echo [INFO] Starting MCP uninstallation...
echo.

:: Step 1: Remove from PYTHONPATH
echo [STEP 1] Removing MCP paths from PYTHONPATH...
set "PYTHONPATH_OLD=%PYTHONPATH%"
set "PYTHONPATH_NEW="

if defined PYTHONPATH (
    for %%p in ("%PYTHONPATH:;=" "%") do (
        set "PATH_ITEM=%%~p"
        set "PATH_ITEM=!PATH_ITEM: =!"
        echo !PATH_ITEM! | findstr /i "%MCP_ROOT%" >nul
        if !errorlevel! neq 0 (
            if defined PYTHONPATH_NEW (
                set "PYTHONPATH_NEW=!PYTHONPATH_NEW!;!PATH_ITEM!"
            ) else (
                set "PYTHONPATH_NEW=!PATH_ITEM!"
            )
        ) else (
            echo [INFO] Removed from PYTHONPATH: !PATH_ITEM!
        )
    )
    
    :: Update system PYTHONPATH
    if defined PYTHONPATH_NEW (
        setx PYTHONPATH "!PYTHONPATH_NEW!" >nul 2>&1
        echo [SUCCESS] PYTHONPATH updated
    ) else (
        reg delete "HKCU\Environment" /v PYTHONPATH /f >nul 2>&1
        echo [SUCCESS] PYTHONPATH cleared
    )
) else (
    echo [INFO] PYTHONPATH not set
)
echo.

:: Step 2: Remove PyXLL add-in from Excel
echo [STEP 2] Removing PyXLL add-in from Excel...

:: Try to unregister PyXLL add-in using PyXLL command
python -c "import pyxll" >nul 2>&1
if !errorlevel!==0 (
    echo [INFO] Unregistering PyXLL add-in...
    python -m pyxll uninstall >nul 2>&1
    if !errorlevel!==0 (
        echo [SUCCESS] PyXLL add-in unregistered successfully
    ) else (
        echo [WARNING] PyXLL add-in unregistration failed
    )
) else (
    echo [INFO] PyXLL module not available, skipping unregistration
)

:: Also remove from Excel startup directories as fallback
set "EXCEL_STARTUP_FOUND=0"
for %%d in ("%APPDATA%\Microsoft\Excel\XLSTART" "%APPDATA%\Microsoft\AddIns" "%ProgramFiles%\Microsoft Office\root\Office16\XLSTART" "%ProgramFiles(x86)%\Microsoft Office\root\Office16\XLSTART") do (
    if exist "%%d" (
        if exist "%%d\pyxll.xll" (
            del "%%d\pyxll.xll" >nul 2>&1
            if !errorlevel!==0 (
                echo [SUCCESS] Removed PyXLL add-in from: %%d
                set "EXCEL_STARTUP_FOUND=1"
            ) else (
                echo [WARNING] Failed to remove PyXLL add-in from: %%d
            )
        )
        
        :: Remove backup files
        if exist "%%d\pyxll.xll.backup" (
            del "%%d\pyxll.xll.backup" >nul 2>&1
            echo [INFO] Removed backup file from: %%d
        )
    )
)

if %EXCEL_STARTUP_FOUND%==0 (
    echo [INFO] No PyXLL add-in found in Excel directories
)
echo.

:: Step 3: Remove desktop shortcut
echo [STEP 3] Removing desktop shortcut...
set "DESKTOP=%USERPROFILE%\Desktop"
if exist "%DESKTOP%\MCP Python Library.url" (
    del "%DESKTOP%\MCP Python Library.url" >nul 2>&1
    if !errorlevel!==0 (
        echo [SUCCESS] Removed desktop shortcut
    ) else (
        echo [WARNING] Failed to remove desktop shortcut
    )
) else (
    echo [INFO] No desktop shortcut found
)
echo.

:: Step 4: Restore pyxll.cfg backups
echo [STEP 4] Restoring pyxll.cfg backups...
for %%d in ("%MCP_ROOT%\lib\X64" "%MCP_ROOT%\lib\Win32") do (
    if exist "%%d\pyxll.cfg.backup" (
        move "%%d\pyxll.cfg.backup" "%%d\pyxll.cfg" >nul 2>&1
        if !errorlevel!==0 (
            echo [SUCCESS] Restored pyxll.cfg backup in %%d
        ) else (
            echo [WARNING] Failed to restore pyxll.cfg backup in %%d
        )
    )
)
echo.

:: Step 5: Test removal
echo [STEP 5] Testing removal...
python -c "import mcp" >nul 2>&1
if !errorlevel!==0 (
    echo [WARNING] MCP library is still importable. PYTHONPATH may not have been updated.
    echo [INFO] Please restart your command prompt and try again.
) else (
    echo [SUCCESS] MCP library is no longer importable
)
echo.

:: Step 6: Cleanup options
echo [STEP 6] Cleanup options...
set /p "DELETE_FILES=Do you want to delete MCP files? (y/N): "
if /i "%DELETE_FILES%"=="y" (
    echo [WARNING] This will permanently delete all MCP files!
    set /p "CONFIRM_DELETE=Are you absolutely sure? (y/N): "
    if /i "!CONFIRM_DELETE!"=="y" (
        echo [INFO] Deleting MCP files...
        cd /d "%MCP_ROOT%\.."
        rmdir /s /q "%MCP_ROOT%" >nul 2>&1
        if !errorlevel!==0 (
            echo [SUCCESS] MCP files deleted
        ) else (
            echo [ERROR] Failed to delete MCP files. Please delete manually.
        )
    ) else (
        echo [INFO] File deletion cancelled
    )
) else (
    echo [INFO] MCP files preserved
)
echo.

echo  ================================================================================
echo.
echo                        UNINSTALLATION COMPLETED
echo.
echo  ================================================================================
echo.

echo [SUCCESS] MCP uninstallation completed!
echo.
echo [INFO] What was removed:
echo   - MCP paths from PYTHONPATH
echo   - PyXLL add-in from Excel
echo   - Desktop shortcut
echo   - pyxll.cfg backups restored
if /i "%DELETE_FILES%"=="y" (
    echo   - MCP files deleted
) else (
    echo   - MCP files preserved
)

echo.
echo [NEXT STEPS]
echo   1. Restart your command prompt or IDE
echo   2. Restart Excel to complete PyXLL removal
echo   3. If you kept the files, you can reinstall by running quick_install.bat
echo.

pause
