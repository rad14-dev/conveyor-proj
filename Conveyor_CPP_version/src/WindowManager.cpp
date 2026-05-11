#include "../include/WindowManager.h"

WindowManager::WindowManager() {}

void WindowManager::RefreshList(const Config& config) {
    lastActiveHwnd = GetForegroundWindow();
    std::vector<HWND> allReal;
    
    auto enumProc = [](HWND hwnd, LPARAM lParam) -> BOOL {
        std::vector<HWND>* list = (std::vector<HWND>*)lParam;
        list->push_back(hwnd);
        return TRUE;
    };
    
    std::vector<HWND> temp;
    EnumWindows(enumProc, (LPARAM)&temp);
    
    managedHwnds.clear();
    for (HWND hwnd : temp) {
        if (Utils::IsRealWindow(hwnd, config.floatingClasses)) {
            bool isFloating = false;
            for (HWND fh : floatingHwnds) if (fh == hwnd) { isFloating = true; break; }
            if (!isFloating) managedHwnds.push_back(hwnd);
        }
    }
    
    RECT wa = Utils::GetWorkArea();
    int sw = wa.right - wa.left;
    
    for (HWND hwnd : managedHwnds) {
        if (windowWidths.find(hwnd) == windowWidths.end()) {
            double factor = Utils::IsHeavyApp(hwnd) ? config.heavyWidthFactor : config.standardWidthFactor;
            windowWidths[hwnd] = (int)(sw * factor);
        }
    }
}

bool WindowManager::SyncStates(const Config& config) {
    std::vector<HWND> temp;
    auto enumProc = [](HWND hwnd, LPARAM lParam) -> BOOL {
        std::vector<HWND>* list = (std::vector<HWND>*)lParam;
        list->push_back(hwnd);
        return TRUE;
    };
    EnumWindows(enumProc, (LPARAM)&temp);
    
    std::vector<HWND> currentList;
    for (HWND hwnd : temp) {
        if (Utils::IsRealWindow(hwnd, config.floatingClasses)) {
            bool isFloating = false;
            for (HWND fh : floatingHwnds) if (fh == hwnd) { isFloating = true; break; }
            if (!isFloating) currentList.push_back(hwnd);
        }
    }
    
    HWND focused = GetForegroundWindow();
    if (currentList == managedHwnds) {
        bool inManaged = false;
        for (HWND h : managedHwnds) if (h == focused) { inManaged = true; break; }
        if (inManaged) lastActiveHwnd = focused;
        return false;
    }
    
    std::vector<HWND> newWindows;
    for (HWND h : currentList) {
        bool exists = false;
        for (HWND mh : managedHwnds) if (mh == h) { exists = true; break; }
        if (!exists) newWindows.push_back(h);
    }
    
    std::vector<HWND> removedWindows;
    for (HWND h : managedHwnds) {
        bool exists = false;
        for (HWND cl : currentList) if (cl == h) { exists = true; break; }
        if (!exists) removedWindows.push_back(h);
    }
    
    // Remove
    for (HWND h : removedWindows) {
        managedHwnds.erase(std::remove(managedHwnds.begin(), managedHwnds.end(), h), managedHwnds.end());
        lastPosCache.erase(h);
    }
    
    // Add
    if (!newWindows.empty()) {
        auto it = std::find(managedHwnds.begin(), managedHwnds.end(), lastActiveHwnd);
        if (it != managedHwnds.end()) {
            managedHwnds.insert(it + 1, newWindows.begin(), newWindows.end());
        } else {
            managedHwnds.insert(managedHwnds.end(), newWindows.begin(), newWindows.end());
        }
    }
    
    if (std::find(managedHwnds.begin(), managedHwnds.end(), focused) != managedHwnds.end()) {
        lastActiveHwnd = focused;
    }
    
    RECT wa = Utils::GetWorkArea();
    int sw = wa.right - wa.left;
    for (HWND h : newWindows) {
        if (windowWidths.find(h) == windowWidths.end()) {
            double factor = Utils::IsHeavyApp(h) ? config.heavyWidthFactor : config.standardWidthFactor;
            windowWidths[h] = (int)(sw * factor);
        }
    }
    
    if (!removedWindows.empty() || !newWindows.empty()) {
        lastPosCache.clear();
        return true;
    }
    return false;
}

void WindowManager::UpdateLayout(int screenWidth, int screenHeight, int workAreaY, int workAreaHeight, double offset_x, int gap) {
    int current_x = (int)(-offset_x);
    int buffer = screenWidth;
    
    for (HWND hwnd : managedHwnds) {
        int w = windowWidths[hwnd];
        if ((current_x + w > -buffer) && (current_x < screenWidth + buffer)) {
            RECT target = {current_x, workAreaY, current_x + w, workAreaY + workAreaHeight};
            RECT last = lastPosCache[hwnd];
            if (last.left != target.left || last.top != target.top || (last.right - last.left) != w || (last.bottom - last.top) != workAreaHeight) {
                Utils::SetWindowPosOptimized(hwnd, current_x, workAreaY, w, workAreaHeight);
                lastPosCache[hwnd] = target;
            }
        }
        current_x += w + gap;
    }
}

void WindowManager::ToggleFloating(HWND hwnd) {
    if (!hwnd) return;
    auto it = std::find(floatingHwnds.begin(), floatingHwnds.end(), hwnd);
    if (it != floatingHwnds.end()) {
        floatingHwnds.erase(it);
        SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);
    } else {
        floatingHwnds.push_back(hwnd);
        SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);
        managedHwnds.erase(std::remove(managedHwnds.begin(), managedHwnds.end(), hwnd), managedHwnds.end());
    }
    lastPosCache.clear();
}

bool WindowManager::SwapWindows(int idx1, int idx2) {
    if (idx1 >= 0 && idx1 < managedHwnds.size() && idx2 >= 0 && idx2 < managedHwnds.size()) {
        std::swap(managedHwnds[idx1], managedHwnds[idx2]);
        lastPosCache.clear();
        return true;
    }
    return false;
}
