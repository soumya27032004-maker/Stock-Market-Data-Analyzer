@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo First double-click start_windows.bat to install packages.
  pause
  exit /b 1
)
echo Opening local dashboard at http://localhost:8501
".venv\Scripts\python.exe" -m streamlit run dashboard.py
pause
