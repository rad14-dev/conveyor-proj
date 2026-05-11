#pragma once
#include "Common.h"

namespace Utils {
    bool IsRealWindow(HWND hwnd, const std::vector<std::string>& floatingClasses);
    bool IsCloaked(HWND hwnd);
    bool IsHeavyApp(HWND hwnd);
    void SetWindowPosOptimized(HWND hwnd, int x, int y, int w, int h);
    RECT GetWorkArea();
    std::string GetWindowTitle(HWND hwnd);
    std::string GetWindowClassName(HWND hwnd);
    double EaseOutCubic(double x);
}
