@echo off
setlocal enabledelayedexpansion

:: --- CONFIGURATION ---
:: You can set your MinGW path here if it's not in your system PATH
:: Example: set "MINGW_PATH=C:\MinGW\bin"
set "USER_MINGW_PATH="

:: --- PREPARE PATH ---
if not "!USER_MINGW_PATH!"=="" (
    set "PATH=!USER_MINGW_PATH!;!PATH!"
)

:: Check if g++ is available
where g++ >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] g++ not found in PATH.
    echo Please install MinGW and add the 'bin' folder to your System PATH,
    echo or edit this script to set your MINGW_PATH.
    pause
    exit /b 1
)

echo Building Conveyor CPP Port...
:: Using %~dp0 to ensure paths are relative to this script
g++ -O3 -s -mwindows "%~dp0src\main.cpp" "%~dp0src\WindowManager.cpp" "%~dp0src\InputHandler.cpp" "%~dp0src\Utils.cpp" -I"%~dp0include" -o "%~dp0Conveyor_CPP.exe" -lgdi32 -lshell32 -static-libgcc -static-libstdc++

if %ERRORLEVEL% EQU 0 (
    echo.
    echo -------------------------------------------
    echo Build Successful: Conveyor_CPP.exe
    echo -------------------------------------------
) else (
    echo.
    echo [ERROR] Build Failed!
)

pause
