@echo off
setlocal enabledelayedexpansion
title AI News Content Analysis - Runner

:menu
cls
echo ==========================================
echo   AI News Content Analysis - Runner
echo ==========================================
echo.
echo  1. [Setup] Initializing/Verify Database
echo  2. [Ingest] Run Full Ingestion (All Sources)
echo  3. [Ingest] VNExpress Only (Limit 50)
echo  4. [Ingest] TuoiTre Only (Limit 50)
echo  5. [Check] Run Diagnostic Checks
echo  6. [Exit] Close Runner
echo.
set /p choice="Select an option (1-6): "

if "%choice%"=="1" goto setup
if "%choice%"=="2" goto ingest_all
if "%choice%"=="3" goto ingest_vn
if "%choice%"=="4" goto ingest_tt
if "%choice%"=="5" goto check
if "%choice%"=="6" exit /b 0

echo.
echo Invalid choice, try again.
timeout /t 2 >nul
goto menu

:setup
echo.
echo [Action] Initializing database...
python -m src.main setup
if %errorlevel% neq 0 (
    echo [Error] Database setup failed.
) else (
    echo [Success] Database is ready.
)
pause
goto menu

:ingest_all
echo.
echo [Action] Running ingestion for all sources...
python -m src.main ingest --source all --limit 50
if %errorlevel% neq 0 (
    echo [Error] Ingestion failed.
) else (
    echo [Success] Ingestion complete.
)
pause
goto menu

:ingest_vn
echo.
echo [Action] Running ingestion for VNExpress...
python -m src.main ingest --source vnexpress --limit 50
pause
goto menu

:ingest_tt
echo.
echo [Action] Running ingestion for TuoiTre...
python -m src.main ingest --source tuoitre --limit 50
pause
goto menu

:check
echo.
echo [Action] Running diagnostic checks...
python -m src.main check
pause
goto menu
