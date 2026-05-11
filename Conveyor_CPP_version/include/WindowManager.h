#pragma once
#include "Common.h"
#include "Utils.h"

class WindowManager {
public:
    WindowManager();
    void RefreshList(const Config& config);
    bool SyncStates(const Config& config);
    void UpdateLayout(int screenWidth, int screenHeight, int workAreaY, int workAreaHeight, double offset_x, int gap);
    void ToggleFloating(HWND hwnd);
    bool SwapWindows(int idx1, int idx2);
    
    std::vector<HWND> managedHwnds;
    std::map<HWND, int> windowWidths;
    std::vector<HWND> floatingHwnds;
    HWND lastActiveHwnd = NULL;

private:
    std::map<HWND, RECT> lastPosCache;
};
