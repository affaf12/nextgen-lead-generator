@echo off
title NextGen Analytics - Lead Generator
color 0B
cd /d "%~dp0"

echo.
echo ============================================
echo   NextGen Analytics - Lead Generator
echo ============================================
echo.

REM --- Check we're in the right folder ---
if not exist "app.py" (
    echo [ERROR] app.py not found. Please put this file inside the project folder and run again.
    pause
    exit /b 1
)
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found. Please put this file inside the project folder and run again.
    pause
    exit /b 1
)

REM --- Check Python is installed ---
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.11 from https://www.python.org/downloads/
    echo IMPORTANT: During install, check "Add python.exe to PATH".
    pause
    exit /b 1
)

echo [1/4] Setting up virtual environment...
if not exist "venv" (
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)
call venv\Scripts\activate.bat

echo [2/4] Installing dependencies...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install requirements. Check your internet connection and try again.
    pause
    exit /b 1
)

echo [3/4] Installing Chromium browser for scraping...
set PLAYWRIGHT_DOWNLOAD_HOST=https://cdn.npmmirror.com/binaries/playwright
python -m playwright install chromium
if errorlevel 1 (
    echo [WARNING] Mirror download failed. Retrying from the official Playwright source...
    set PLAYWRIGHT_DOWNLOAD_HOST=
    python -m playwright install chromium
    if errorlevel 1 (
        echo.
        echo ============================================
        echo   [ERROR] Chromium install FAILED.
        echo   Scraping will NOT work until this is fixed.
        echo ============================================
        echo.
        echo Try one of these, then run this file again:
        echo   1. Connect to a VPN or Cloudflare WARP ^(https://1.1.1.1/^)
        echo   2. Run manually:
        echo        venv\Scripts\activate
        echo        python -m playwright install chromium
        echo.
        pause
        exit /b 1
    )
)

echo [4/4] Starting the app...
echo.
echo Dashboard will open in your browser shortly at http://127.0.0.1:5000
echo Keep this window open while you use the app.
echo Close this window ^(or press CTRL+C^) to stop the app.
echo.

REM --- Give Flask a moment to boot before opening the browser, so it doesn't
REM     load before the server is ready ---
start "" cmd /c "timeout /t 4 >nul && start http://127.0.0.1:5000"

python app.py

pause
