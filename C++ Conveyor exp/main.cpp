#define _WIN32_WINNT 0x0600
#include <windows.h>
#include <shellapi.h>
#include <iostream>
#include <vector>
#include <string>
#include <cstring>
#include <algorithm>
#include <map>
#include <cmath>

// Definisi Tray
#define WM_TRAYICON (WM_USER + 1)
#define ID_TRAY_EXIT 1001

// Definisi konstanta DWM jika tidak ada
#ifndef DWMWA_CLOAKED
#define DWMWA_CLOAKED 14
#endif

typedef HRESULT (WINAPI *DwmGetWindowAttributePtr)(HWND, DWORD, PVOID, DWORD);

struct WindowData {
    HWND hwnd;
    std::string title;
    int width;
    bool isFloating = false;
    WindowData(HWND h, std::string t, int w, bool f) : hwnd(h), title(t), width(w), isFloating(f) {}
};

// Global State
std::vector<WindowData> managedWindows;
std::map<HWND, int> windowWidths;
std::vector<HWND> floatingWindows;

double currentOffsetX = 0.0;
double targetOffsetX = 0.0;
double lerpFactor = 0.15;
int windowGap = 10;
int screenWidth = 0;
int screenHeight = 0;
int workAreaY = 0;
int workAreaHeight = 0;
DWORD lastInputTime = 0;
const int snapDelay = 200;
bool pendingSync = false;
HWND lastActiveHwnd = NULL;
NOTIFYICONDATAA nid = {0};

// Forward Declarations
void UpdateLayout();
void SyncStates();

bool IsRealWindow(HWND hwnd) {
    if (!IsWindowVisible(hwnd) || IsIconic(hwnd)) return false;
    
    // Abaikan jendela yang punya "Owner" (biasanya dialog atau popup anak)
    if (GetWindow(hwnd, GW_OWNER) != NULL) return false;

    LONG exStyle = GetWindowLong(hwnd, GWL_EXSTYLE);
    LONG style = GetWindowLong(hwnd, GWL_STYLE);

    // Filter ToolWindows dan Jendela tanpa Border/Caption (biasanya overlay)
    if (exStyle & WS_EX_TOOLWINDOW) return false;
    if (!(style & WS_CAPTION)) return false;

    static HMODULE hDwm = LoadLibraryA("dwmapi.dll");
    if (hDwm) {
        static DwmGetWindowAttributePtr pDwmGetWindowAttribute = 
            (DwmGetWindowAttributePtr)GetProcAddress(hDwm, "DwmGetWindowAttribute");
        if (pDwmGetWindowAttribute) {
            int cloaked = 0;
            if (pDwmGetWindowAttribute(hwnd, DWMWA_CLOAKED, &cloaked, sizeof(cloaked)) == S_OK) {
                if (cloaked != 0) return false;
            }
        }
    }

    char title[512] = {0};
    GetWindowTextA(hwnd, title, sizeof(title));
    if (strlen(title) == 0 || strstr(title, "Conveyor") != NULL) return false;

    char className[256];
    GetClassNameA(hwnd, className, sizeof(className));
    std::string cls = className;
    
    // Daftar kelas sistem yang harus diabaikan
    if (cls == "Shell_TrayWnd" || cls == "Progman" || cls == "WorkerW" || 
        cls == "Windows.UI.Core.CoreWindow" || cls == "SearchUI.exe") return false;
        
    return true;
}

bool IsFloating(HWND hwnd) {
    return std::find(floatingWindows.begin(), floatingWindows.end(), hwnd) != floatingWindows.end();
}

void UpdateLayout() {
    int currentX = (int)(-currentOffsetX);
    for (auto& win : managedWindows) {
        if (!IsWindow(win.hwnd)) continue;
        int w = windowWidths[win.hwnd];
        SetWindowPos(win.hwnd, HWND_TOP, currentX, workAreaY, w, workAreaHeight, 
                     SWP_NOACTIVATE | SWP_NOOWNERZORDER | SWP_ASYNCWINDOWPOS | SWP_NOCOPYBITS | SWP_FRAMECHANGED);
        currentX += w + windowGap;
    }
}

double GetSnapTarget() {
    if (managedWindows.empty()) return 0;
    int totalWidth = 0;
    for (auto& win : managedWindows) totalWidth += windowWidths[win.hwnd] + windowGap;
    totalWidth -= windowGap;
    double maxOffset = std::max(0, totalWidth - screenWidth);
    double clampedTarget = std::max(0.0, std::min(maxOffset, targetOffsetX));
    double bestOffset = clampedTarget;
    double minDict = 1e9;
    int accX = 0;
    for (auto& win : managedWindows) {
        int w = windowWidths[win.hwnd];
        double snapPos = (accX + w / 2.0) - (screenWidth / 2.0);
        snapPos = std::max(0.0, std::min(maxOffset, snapPos));
        double dist = std::abs(targetOffsetX - snapPos);
        if (dist < minDict) { minDict = dist; bestOffset = snapPos; }
        accX += w + windowGap;
    }
    return bestOffset;
}

BOOL CALLBACK EnumWindowsCallback(HWND hwnd, LPARAM lParam) {
    if (IsRealWindow(hwnd) && !IsFloating(hwnd)) {
        ((std::vector<HWND>*)lParam)->push_back(hwnd);
    }
    return TRUE;
}

void SyncStates() {
    std::vector<HWND> currentList;
    EnumWindows(EnumWindowsCallback, (LPARAM)&currentList);

    std::vector<WindowData> oldList = managedWindows;
    if (currentList.size() == oldList.size()) {
        bool changed = false;
        for (size_t i = 0; i < currentList.size(); i++) {
            if (currentList[i] != oldList[i].hwnd) { changed = true; break; }
        }
        if (!changed) return;
    }

    std::vector<HWND> newHwnds;
    for (HWND hwnd : currentList) {
        bool exists = false;
        for (const auto& win : oldList) if (win.hwnd == hwnd) { exists = true; break; }
        if (!exists) newHwnds.push_back(hwnd);
    }

    std::vector<WindowData> workingList = oldList;
    workingList.erase(std::remove_if(workingList.begin(), workingList.end(), [&](const WindowData& win){
        return std::find(currentList.begin(), currentList.end(), win.hwnd) == currentList.end();
    }), workingList.end());

    HWND active = GetForegroundWindow();
    for (HWND hwnd : newHwnds) {
        if (windowWidths.find(hwnd) == windowWidths.end()) windowWidths[hwnd] = (int)(screenWidth * 0.5);
        char title[512] = {0};
        GetWindowTextA(hwnd, title, sizeof(title));
        WindowData newData(hwnd, title, windowWidths[hwnd], false);
        int insertIdx = -1;
        for (int i = 0; i < workingList.size(); i++) if (workingList[i].hwnd == lastActiveHwnd) { insertIdx = i; break; }
        if (insertIdx != -1) workingList.insert(workingList.begin() + insertIdx + 1, newData);
        else workingList.push_back(newData);
    }
    managedWindows = workingList;
    UpdateLayout();
}

LRESULT CALLBACK KeyboardHookProc(int nCode, WPARAM wParam, LPARAM lParam) {
    if (nCode == HC_ACTION && (wParam == WM_KEYDOWN || wParam == WM_SYSKEYDOWN)) {
        KBDLLHOOKSTRUCT* pKeyStruct = (KBDLLHOOKSTRUCT*)lParam;
        bool winPressed = (GetAsyncKeyState(VK_LWIN) & 0x8000) || (GetAsyncKeyState(VK_RWIN) & 0x8000);
        bool altPressed = (GetAsyncKeyState(VK_MENU) & 0x8000);
        if (altPressed) {
            HWND active = GetForegroundWindow();
            int vkCode = pKeyStruct->vkCode;
            if (vkCode >= '1' && vkCode <= '4') {
                double factors[] = {0.25, 0.5, 0.75, 1.0};
                int newWidth = (int)(screenWidth * factors[vkCode - '1']);
                windowWidths[active] = newWidth;
                for (auto& win : managedWindows) if (win.hwnd == active) win.width = newWidth;
                UpdateLayout();
                return 1;
            }
            if (winPressed) {
                if (vkCode == 'V') {
                    auto it = std::find(floatingWindows.begin(), floatingWindows.end(), active);
                    if (it != floatingWindows.end()) floatingWindows.erase(it);
                    else floatingWindows.push_back(active);
                    SyncStates(); return 1;
                }
                auto it = std::find_if(managedWindows.begin(), managedWindows.end(), [active](const WindowData& w){ return w.hwnd == active; });
                if (it != managedWindows.end()) {
                    int idx = std::distance(managedWindows.begin(), it);
                    if (vkCode == VK_OEM_COMMA && idx > 0) { std::swap(managedWindows[idx], managedWindows[idx - 1]); UpdateLayout(); return 1; }
                    if (vkCode == VK_OEM_PERIOD && idx < managedWindows.size() - 1) { std::swap(managedWindows[idx], managedWindows[idx + 1]); UpdateLayout(); return 1; }
                }
                if (vkCode == VK_LEFT || vkCode == VK_RIGHT || vkCode == 'M' || vkCode == 'N') {
                    targetOffsetX += (vkCode == VK_LEFT || vkCode == 'N') ? -200 : 200;
                    lastInputTime = GetTickCount();
                    return 1;
                }
            }
        }
    }
    return CallNextHookEx(NULL, nCode, wParam, lParam);
}

LRESULT CALLBACK MouseHookProc(int nCode, WPARAM wParam, LPARAM lParam) {
    if (nCode == HC_ACTION && wParam == WM_MOUSEWHEEL) {
        MSLLHOOKSTRUCT* pMouseStruct = (MSLLHOOKSTRUCT*)lParam;
        if (((GetAsyncKeyState(VK_LWIN) & 0x8000) || (GetAsyncKeyState(VK_RWIN) & 0x8000)) && (GetAsyncKeyState(VK_MENU) & 0x8000)) {
            targetOffsetX -= (GET_WHEEL_DELTA_WPARAM(pMouseStruct->mouseData) * 2.5);
            lastInputTime = GetTickCount(); return 1;
        }
    }
    return CallNextHookEx(NULL, nCode, wParam, lParam);
}

LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    if (msg == WM_TRAYICON) {
        if (lParam == WM_RBUTTONUP) {
            POINT pt; GetCursorPos(&pt);
            HMENU hMenu = CreatePopupMenu();
            AppendMenuA(hMenu, MF_STRING, ID_TRAY_EXIT, "Exit Conveyor");
            SetForegroundWindow(hwnd);
            TrackPopupMenu(hMenu, TPM_BOTTOMALIGN | TPM_LEFTALIGN, pt.x, pt.y, 0, hwnd, NULL);
            DestroyMenu(hMenu);
        }
    } else if (msg == WM_COMMAND) {
        if (LOWORD(wParam) == ID_TRAY_EXIT) {
            Shell_NotifyIconA(NIM_DELETE, &nid);
            PostQuitMessage(0);
        }
    } else if (msg == WM_DESTROY) {
        Shell_NotifyIconA(NIM_DELETE, &nid);
        PostQuitMessage(0);
    }
    return DefWindowProc(hwnd, msg, wParam, lParam);
}

int main() {
    // Memberitahu Windows bahwa aplikasi ini mendukung High DPI (scaling)
    SetProcessDPIAware();

    HINSTANCE hInstance = GetModuleHandle(NULL);
    std::cout << "[Conveyor] Starting..." << std::endl;
    WNDCLASSA wc = {0};
    wc.lpfnWndProc = WndProc;
    wc.hInstance = hInstance;
    wc.lpszClassName = "ConveyorTrayClass";
    RegisterClassA(&wc);
    HWND hHiddenWnd = CreateWindowA(wc.lpszClassName, "Conveyor Tray", 0, 0, 0, 0, 0, NULL, NULL, hInstance, NULL);

    nid.cbSize = sizeof(NOTIFYICONDATAA);
    nid.hWnd = hHiddenWnd;
    nid.uID = 1;
    nid.uFlags = NIF_ICON | NIF_MESSAGE | NIF_TIP;
    nid.uCallbackMessage = WM_TRAYICON;
    nid.hIcon = LoadIcon(NULL, IDI_APPLICATION);
    strcpy(nid.szTip, "Conveyor Window Manager");
    if (!Shell_NotifyIconA(NIM_ADD, &nid)) {
        std::cout << "[Warning] Tray icon failed to create." << std::endl;
    }

    std::cout << "[Conveyor] Initializing metrics..." << std::endl;

    screenWidth = GetSystemMetrics(SM_CXSCREEN);
    screenHeight = GetSystemMetrics(SM_CYSCREEN);
    RECT workArea;
    if (SystemParametersInfo(SPI_GETWORKAREA, 0, &workArea, 0)) {
        workAreaY = workArea.top; workAreaHeight = workArea.bottom - workArea.top;
    } else {
        workAreaY = 0; workAreaHeight = screenHeight;
    }

    std::cout << "[Conveyor] Syncing initial state..." << std::endl;
    SyncStates();
    
    std::cout << "[Conveyor] Setting hooks..." << std::endl;
    HHOOK hMouseHook = SetWindowsHookEx(WH_MOUSE_LL, MouseHookProc, GetModuleHandle(NULL), 0);
    HHOOK hKeyHook = SetWindowsHookEx(WH_KEYBOARD_LL, KeyboardHookProc, GetModuleHandle(NULL), 0);

    if (!hMouseHook || !hKeyHook) {
        std::cout << "[Error] Failed to set hooks!" << std::endl;
    } else {
        std::cout << "[Conveyor] Running. Use Tray Icon to exit." << std::endl;
    }

    MSG msg;
    while (true) {
        while (PeekMessage(&msg, NULL, 0, 0, PM_REMOVE)) {
            if (msg.message == WM_QUIT) goto cleanup;
            TranslateMessage(&msg); DispatchMessage(&msg);
        }

        HWND foreground = GetForegroundWindow();
        if (foreground && IsRealWindow(foreground)) lastActiveHwnd = foreground;

        DWORD now = GetTickCount();
        static DWORD lastSync = 0;
        if (pendingSync || (now - lastSync > 2000)) { SyncStates(); pendingSync = false; lastSync = now; }
        
        double diff = targetOffsetX - currentOffsetX;
        if (std::abs(diff) > 0.1) {
            currentOffsetX += diff * lerpFactor; UpdateLayout();
        } else if (std::abs(diff) > 0) {
            currentOffsetX = targetOffsetX; UpdateLayout();
        } else {
            currentOffsetX = targetOffsetX;
            bool modifiersActive = ((GetAsyncKeyState(VK_LWIN) & 0x8000) || (GetAsyncKeyState(VK_RWIN) & 0x8000)) && (GetAsyncKeyState(VK_MENU) & 0x8000);
            if (!modifiersActive && (now - lastInputTime > snapDelay)) {
                double snapTarget = GetSnapTarget();
                if (std::abs(targetOffsetX - snapTarget) > 1.0) targetOffsetX = snapTarget;
            }
        }
        Sleep(16); // ~60 FPS - better for low end CPU
    }

cleanup:
    UnhookWindowsHookEx(hMouseHook);
    UnhookWindowsHookEx(hKeyHook);
    return 0;
}

