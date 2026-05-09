@echo off
set "PATH=E:\Bengkel Digital\Min GW\bin;%PATH%"
echo [Conveyor C++] Compiling main.cpp...
g++ main.cpp -o ConveyorV2.exe -luser32 -lgdi32 -lshell32 -std=c++11 -static-libgcc -static-libstdc++ -static
if %errorlevel% neq 0 (
    echo Compilation failed. Make sure g++ ^(MinGW^) is installed and in your PATH.
) else (
    echo Compilation successful! Running ConveyorV2.exe...
    ConveyorV2.exe
)
pause
