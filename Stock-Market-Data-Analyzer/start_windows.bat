@echo off
setlocal
cd /d "%~dp0"
echo ========================================
echo  Stock Market Data Analyzer - SETUP
 echo ========================================
py -3 --version >nul 2>nul
if %errorlevel%==0 (
  set "PYTHON=py -3"
) else (
  python --version >nul 2>nul
  if %errorlevel% neq 0 (
    echo Python was not found.
    echo Install Python from https://www.python.org/downloads/windows/
    echo Select Add python.exe to PATH during installation.
    echo Restart Command Prompt, then run this file again.
    pause
    exit /b 1
  )
  set "PYTHON=python"
)
if not exist ".venv\Scripts\python.exe" (
  echo Creating local Python environment...
  %PYTHON% -m venv .venv
  if errorlevel 1 ( echo Could not create Python environment. & pause & exit /b 1 )
)
echo Installing packages (first time may require internet)...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 ( echo Package install failed. Check your internet and Python version. & pause & exit /b 1 )
echo Running OFFLINE sample analysis...
".venv\Scripts\python.exe" main.py
if errorlevel 1 ( echo Analysis failed; see error above. & pause & exit /b 1 )
echo.
echo SUCCESS. Open the reports and outputs folders to view results.
echo To open the dashboard next, double-click dashboard_windows.bat
pause
