@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (echo Run setup.bat first.&pause&exit /b 1)
call .venv\Scripts\activate.bat
pyinstaller --noconfirm --clean --windowed --name EGG_FARM_GATUZ --collect-all customtkinter main.py
echo Executable bundle is in dist\EGG_FARM_GATUZ
pause
