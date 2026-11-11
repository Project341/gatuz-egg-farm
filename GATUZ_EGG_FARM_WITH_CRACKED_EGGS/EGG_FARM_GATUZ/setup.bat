@echo off
setlocal
cd /d "%~dp0"
title GATUZ EGG FARM - Setup
where py >nul 2>nul || (echo Python Launcher not found. Install Python 3.14 and enable Add Python to PATH.&pause&exit /b 1)
if not exist ".venv\Scripts\python.exe" (
  py -3.14 -m venv .venv
  if errorlevel 1 py -3 -m venv .venv
  if errorlevel 1 (echo Could not create virtual environment.&pause&exit /b 1)
)
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (echo Could not update pip.&pause&exit /b 1)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (echo Package installation failed. Check internet connection and retry.&pause&exit /b 1)
".venv\Scripts\python.exe" -c "import customtkinter; print('CustomTkinter installed successfully:', customtkinter.__version__)"
if errorlevel 1 (echo CustomTkinter verification failed.&pause&exit /b 1)
echo Setup complete. You can now use run.bat.
pause
