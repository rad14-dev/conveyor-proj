#include "../include/Utils.h"

namespace Utils {

bool IsCloaked(HWND hwnd) {
    int cloaked = 0;
    HRESULT hr = DwmGetWindowAttribute(hwnd, DWMWA_CLOAKED, &cloaked, sizeof(cloaked));
    return (hr == S_OK && cloaked != 0);
}

bool IsHeavyApp(HWND hwnd) {
    std::string title = GetWindowTitle(hwnd);
    std::string cls = GetWindowClassName(hwnd);
    std::transform(title.begin(), title.end(), title.begin(), ::tolower);
    std::transform(cls.begin(), cls.end(), cls.begin(), ::tolower);

    const char* heavy[] = {"affinity", "photoshop", "illustrator", "premiere", "blender", "figma"};
    for (const char* k : heavy) {
        if (title.find(k) != std::string::npos || cls.find(k) != std::string::npos) return true;
    }
    return false;
}

std::string GetWindowTitle(HWND hwnd) {
    char buf[512];
    GetWindowTextA(hwnd, buf, sizeof(buf));
    return std::string(buf);
}

std::string GetWindowClassName(HWND hwnd) {
    char buf[256];
    GetClassNameA(hwnd, buf, sizeof(buf));
    return std::string(buf);
}

bool IsRealWindow(HWND hwnd, const std::vector<std::string>& floatingClasses) {
    if (!IsWindowVisible(hwnd) || IsIconic(hwnd)) return false;

    std::string title = GetWindowTitle(hwnd);
    std::string cls = GetWindowClassName(hwnd);
    bool isChrome = (cls == "Chrome_WidgetWin_1");

    if (IsCloaked(hwnd) && !(isChrome && !title.empty())) return false;

    if (GetWindow(hwnd, GW_OWNER) != NULL) {
        if (!(isChrome && !title.empty())) return false;
    }

    if (title.empty()) return false;
    if (title == "Conveyor Runner" || title == "Conveyor Tray") return false;

    LONG style = GetWindowLong(hwnd, GWL_STYLE);
    LONG exStyle = GetWindowLong(hwnd, GWL_EXSTYLE);

    if (exStyle & WS_EX_TOOLWINDOW) return false;
    if ((style & WS_POPUP) && !(style & WS_THICKFRAME)) return false;

    const char* blockedClasses[] = {"Shell_TrayWnd", "Progman", "WorkerW", "Windows.UI.Core.CoreWindow", "SearchUI.exe", "GhostWnd"};
    for (const char* bc : blockedClasses) if (cls == bc) return false;

    const char* blockedTitles[] = {"Start", "Search", "Task View"};
    for (const char* bt : blockedTitles) if (title == bt) return false;

    for (const auto& fc : floatingClasses) if (cls == fc) return false;

    return true;
}

void SetWindowPosOptimized(HWND hwnd, int x, int y, int w, int h) {
    SetWindowPos(hwnd, NULL, x, y, w, h, 
                 SWP_NOACTIVATE | SWP_ASYNCWINDOWPOS | SWP_NOZORDER | SWP_NOCOPYBITS);
}

RECT GetWorkArea() {
    RECT rect;
    SystemParametersInfoW(SPI_GETWORKAREA, 0, &rect, 0);
    return rect;
}

double EaseOutCubic(double x) {
    return 1.0 - std::pow(1.0 - x, 3);
}

}
