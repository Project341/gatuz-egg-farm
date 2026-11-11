@echo off
setlocal
cd /d "%~dp0"
title GATUZ EGG FARM
if not exist ".venv\Scripts\python.exe" (
  echo Application environment not found. Starting setup...
  call setup.bat
  if not exist ".venv\Scripts\python.exe" exit /b 1
)
".venv\Scripts\python.exe" -c "import customtkinter" >nul 2>nul
if errorlevel 1 (
  echo CustomTkinter is missing. Installing application requirements...
  call setup.bat
  if errorlevel 1 exit /b 1
)
".venv\Scripts\python.exe" main.py
if errorlevel 1 (
  echo.
  echo Application error. Please take a screenshot of this window and send it for support.
  pause
)
