@echo off
title PMS Engine - Frontend
echo ============================================
echo   PMS Engine Frontend (Vite + React)
echo ============================================
echo.

cd /d "%~dp0frontend"

REM 1. Verify npm is available on system
where npm >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Node.js / npm is not installed or not added to your system PATH.
    echo Please install Node.js (v20+ LTS recommended) to run the frontend.
    echo.
    pause
    exit /b
)

REM 2. Install node dependencies if node_modules is missing
if not exist "node_modules" (
    echo [INFO] node_modules not found. Installing frontend dependencies...
    echo [INFO] Running npm install (this might take a few moments)...
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install frontend dependencies. Please check package.json.
        pause
        exit /b
    )
    echo [SUCCESS] Frontend dependencies installed successfully.
    echo.
) else (
    echo [INFO] Frontend dependencies (node_modules) already found.
    echo.
)

echo [INFO] Starting Vite dev server...
echo [INFO] App will be available at: http://localhost:5173
echo.
npm run dev

pause
