@echo off
title PMS Engine - Backend
echo ============================================
echo   PMS Engine Backend (FastAPI + Uvicorn)
echo ============================================
echo.

cd /d "%~dp0backend"

REM 1. Verify python is available on system
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python is not installed or not added to your system PATH.
    echo Please install Python 3.10+ to run the backend.
    echo.
    pause
    exit /b
)

REM 2. Create .env from example if it doesn't exist
if not exist ".env" (
    if exist ".env.example" (
        echo [INFO] Creating backend .env from .env.example...
        copy ".env.example" ".env" >nul
    )
)

REM 3. Check if venv python executable is valid
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe -c "import sys" 2>nul
    if errorlevel 1 (
        echo [WARN] Virtual environment is broken (Python path mismatch). Recreating...
        rmdir /s /q venv
    )
)

REM 4. Create virtual environment if missing
if not exist "venv\Scripts\python.exe" (
    echo [INFO] Creating Python virtual environment (venv)...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b
    )
    echo [SUCCESS] Virtual environment created successfully.
    echo.
)

REM 5. Verify and install requirements
venv\Scripts\python.exe -c "import fastapi, uvicorn, pandas, pydantic, yfinance" 2>nul
if errorlevel 1 (
    echo [INFO] Installing/upgrading backend library dependencies (requirements.txt)...
    echo [INFO] Upgrading pip...
    venv\Scripts\python.exe -m pip install --upgrade pip --quiet
    echo [INFO] Running pip install (this might take a few moments)...
    venv\Scripts\pip.exe install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install backend dependencies. Please check requirements.txt.
        pause
        exit /b
    )
    echo [SUCCESS] Backend dependencies installed successfully.
    echo.
) else (
    echo [INFO] Backend dependencies already satisfied.
)

echo [INFO] Starting FastAPI server...
echo [INFO] API Docs will be available at: http://localhost:8000/api/docs
echo.
venv\Scripts\python.exe main.py

pause
