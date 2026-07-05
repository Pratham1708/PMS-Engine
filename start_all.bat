@echo off
title PMS Engine - Launcher
echo ============================================
echo   PMS Engine - Full Stack Launcher
echo ============================================
echo.

REM 1. Check for Python installation
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found on your system PATH.
    echo Please install Python 3.10 or higher.
    echo IMPORTANT: Make sure to check "Add Python to PATH" during setup.
    echo Download link: https://www.python.org/downloads/
    echo.
    pause
    exit /b
)

REM 2. Check for Node.js / npm installation
where npm >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Node.js / npm was not found on your system PATH.
    echo Please install Node.js (v20+ LTS recommended).
    echo Download link: https://nodejs.org/
    echo.
    pause
    exit /b
)

REM 3. Ensure root configuration template .env exists
if not exist ".env" (
    if exist ".env.example" (
        echo [INFO] Creating root .env from .env.example...
        copy ".env.example" ".env" >nul
    )
)

echo [INFO] Prerequisites check passed!
echo [INFO] Opening Backend in a new terminal...
start "PMS Engine - Backend" cmd /k ""%~dp0start_backend.bat""

REM Brief pause so backend terminal opens first
timeout /t 2 /nobreak >nul

echo [INFO] Opening Frontend in a new terminal...
start "PMS Engine - Frontend" cmd /k ""%~dp0start_frontend.bat""

echo.
echo [SUCCESS] Both servers are starting in separate windows.
echo.
echo   Backend API:  http://localhost:8000/api/docs
echo   Frontend App: http://localhost:5173
echo.
echo This window can be closed safely.
pause
