@echo off
setlocal
cd /d "%~dp0"
title GATUZ EGG FARM - Installer and Launcher

echo ================================================
echo       GATUZ EGG FARM MANAGEMENT SYSTEM
echo          Automatic setup and launch
echo ================================================
echo.

where py >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python Launcher was not found.
  echo Install Python 3.14 from https://www.python.org/downloads/windows/
  echo During installation, enable Python Launcher and Add Python to PATH.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [1/4] Creating a private Python environment...
  py -3.14 -m venv .venv
  if errorlevel 1 (
    echo Python 3.14 was not found. Trying the default Python installation...
    py -3 -m venv .venv
  )
  if errorlevel 1 (
    echo ERROR: Could not create the virtual environment.
    pause
    exit /b 1
  )
)

echo.
echo [2/4] Updating pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto install_error

echo.
echo [3/4] Installing required application packages...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto install_error

echo.
echo [4/4] Checking CustomTkinter installation...
".venv\Scripts\python.exe" -c "import customtkinter; print('CustomTkinter OK:', customtkinter.__version__)"
if errorlevel 1 goto install_error

echo.
echo Setup complete. Opening GATUZ EGG FARM...
echo.
".venv\Scripts\python.exe" main.py
if errorlevel 1 (
  echo.
  echo The application stopped because of an error. Please take a screenshot of this window.
  pause
)
exit /b

:install_error
echo.
echo INSTALLATION FAILED.
echo Check your internet connection, then run SETUP_AND_RUN.bat again.
echo If it still fails, send a screenshot of the full error above.
pause
exit /b 1
