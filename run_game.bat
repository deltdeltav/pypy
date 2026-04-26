@echo off
echo ==================================
echo    DELTA CORE: PRO - Launcher
echo ==================================
echo.
echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.10+ from https://python.org
    echo.
    pause
    exit /b 1
)

echo Installing requirements...
python -m pip install -r requirements.txt --user

echo.
echo Starting game...
python main.py
pause
