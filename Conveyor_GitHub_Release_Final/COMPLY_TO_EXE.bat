@echo off
title Conveyor v0.12.3 Compiler
echo ======================================================
echo       CONVEYOR v0.12.3 - FINAL BUILD SYSTEM
echo ======================================================
echo.
echo [1/3] Menginstal dependensi yang diperlukan...
pip install pyinstaller pynput pywin32
echo.
echo [2/3] Memulai kompilasi ke EXE (Mode: Windowed, One-File)...
echo.
pyinstaller --noconfirm --onefile --windowed --add-data "conveyor_config.json;." --name "Conveyor_v0.12.3" main.py
echo.
echo [3/3] Membersihkan file sementara...
rmdir /s /q build
del /f /q Conveyor_v0.12.3.spec
echo.
echo ======================================================
echo   BERHASIL! File EXE Anda ada di dalam folder 'dist'.
echo   Pindahkan file EXE tersebut keluar bersama dengan 
echo   'conveyor_config.json' untuk dijalankan.
echo ======================================================
pause
