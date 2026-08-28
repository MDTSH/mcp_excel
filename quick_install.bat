@echo off
chcp 65001 >nul
cd /d "%~dp0"
call "%~dp0install.bat" %*
exit /b %errorlevel%
