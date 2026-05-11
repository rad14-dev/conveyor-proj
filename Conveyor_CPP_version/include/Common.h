#pragma once
#define _WIN32_WINNT 0x0600
#include <windows.h>
#include <shellapi.h>
#include <dwmapi.h>
#include <iostream>
#include <vector>
#include <string>
#include <map>
#include <algorithm>
#include <cmath>
#include <chrono>
#include <thread>

#pragma comment(lib, "user32.lib")
#pragma comment(lib, "shell32.lib")
#pragma comment(lib, "dwmapi.lib")
#pragma comment(lib, "gdi32.lib")

#define WM_TRAYICON (WM_USER + 1)
#define ID_TRAY_EXIT 1001
#define ID_TRAY_SHOW 1002

struct WindowData {
    HWND hwnd;
    std::string title;
    std::string className;
    int width;
    bool isFloating;
};

struct Config {
    int windowGap = 10;
    double standardWidthFactor = 0.5;
    double heavyWidthFactor = 0.75;
    std::vector<std::string> floatingClasses;
    // Shortcuts could be added here
};
