@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto install
python -c "import sys; assert sys.version_info >= (3,10)" >nul 2>nul
if errorlevel 1 (
    py -3 -m venv .venv
) else (
    python -m venv .venv
)
if errorlevel 1 goto failed
:install
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -c "import pygame,numpy" >nul 2>nul
if errorlevel 1 goto failed
echo Setup complete.
if /I not "%~1"=="--quiet" pause
exit /b 0
:failed
echo Setup failed. Python 3.10 or newer is required.
if /I not "%~1"=="--quiet" pause
exit /b 1
