@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto local
if exist "..\.venv\Scripts\python.exe" (
    "..\.venv\Scripts\python.exe" -c "import pygame,numpy" >nul 2>nul
    if not errorlevel 1 (
        "..\.venv\Scripts\python.exe" tree.py %*
        goto finished
    )
)
if exist "..\..\.venv\Scripts\python.exe" (
    "..\..\.venv\Scripts\python.exe" -c "import pygame,numpy" >nul 2>nul
    if not errorlevel 1 (
        "..\..\.venv\Scripts\python.exe" tree.py %*
        goto finished
    )
)
:install
call setup.bat --quiet
if errorlevel 1 goto failed
:local
".venv\Scripts\python.exe" -c "import pygame,numpy" >nul 2>nul
if errorlevel 1 goto install
".venv\Scripts\python.exe" tree.py %*
:finished
if errorlevel 1 goto failed
exit /b 0
:failed
echo Could not start Christmas. Check the error above.
pause
exit /b 1
