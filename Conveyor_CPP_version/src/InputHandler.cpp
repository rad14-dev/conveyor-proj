#include "../include/InputHandler.h"
#include "../include/WindowManager.h"
#include "../include/Utils.h"

HHOOK InputHandler::hKeyHook = NULL;
HHOOK InputHandler::hMouseHook = NULL;

extern WindowManager g_wm;
extern Config g_config;
extern double g_targetOffsetX;
extern double g_currentOffsetX;
extern DWORD g_lastInputTime;
extern bool g_pendingSync;

void InputHandler::Start() {
    hKeyHook = SetWindowsHookEx(WH_KEYBOARD_LL, LowLevelKeyboardProc, GetModuleHandle(NULL), 0);
    hMouseHook = SetWindowsHookEx(WH_MOUSE_LL, LowLevelMouseProc, GetModuleHandle(NULL), 0);
}

void InputHandler::Stop() {
    if (hKeyHook) UnhookWindowsHookEx(hKeyHook);
    if (hMouseHook) UnhookWindowsHookEx(hMouseHook);
}

bool InputHandler::AreModifiersActive() {
    bool win = (GetAsyncKeyState(VK_LWIN) & 0x8000) || (GetAsyncKeyState(VK_RWIN) & 0x8000);
    bool alt = (GetAsyncKeyState(VK_MENU) & 0x8000);
    return win && alt;
}

LRESULT CALLBACK InputHandler::LowLevelKeyboardProc(int nCode, WPARAM wParam, LPARAM lParam) {
    if (nCode == HC_ACTION && (wParam == WM_KEYDOWN || wParam == WM_SYSKEYDOWN)) {
        KBDLLHOOKSTRUCT* p = (KBDLLHOOKSTRUCT*)lParam;
        bool modActive = AreModifiersActive();
        bool altOnly = (GetAsyncKeyState(VK_MENU) & 0x8000);
        HWND active = GetForegroundWindow();

        if (altOnly) {
            if (p->vkCode == 'Q') {
                g_pendingSync = true;
                return 1;
            }
            if (p->vkCode >= '1' && p->vkCode <= '4') {
                double factors[] = {0.25, 0.5, 0.75, 1.0};
                RECT wa = Utils::GetWorkArea();
                int sw = wa.right - wa.left;
                g_wm.windowWidths[active] = (int)(sw * factors[p->vkCode - '1']);
                return 1;
            }
        }

        if (modActive) {
            if (p->vkCode == 'V') {
                g_wm.ToggleFloating(active);
                return 1;
            }
            
            auto it = std::find(g_wm.managedHwnds.begin(), g_wm.managedHwnds.end(), active);
            if (it != g_wm.managedHwnds.end()) {
                int idx = std::distance(g_wm.managedHwnds.begin(), it);
                if (p->vkCode == VK_OEM_COMMA) { g_wm.SwapWindows(idx, idx - 1); return 1; }
                if (p->vkCode == VK_OEM_PERIOD) { g_wm.SwapWindows(idx, idx + 1); return 1; }
            }

            if (p->vkCode == VK_LEFT || p->vkCode == 'N') { g_targetOffsetX -= 300; g_lastInputTime = GetTickCount(); return 1; }
            if (p->vkCode == VK_RIGHT || p->vkCode == 'M') { g_targetOffsetX += 300; g_lastInputTime = GetTickCount(); return 1; }
        }
    }
    return CallNextHookEx(NULL, nCode, wParam, lParam);
}

LRESULT CALLBACK InputHandler::LowLevelMouseProc(int nCode, WPARAM wParam, LPARAM lParam) {
    if (nCode == HC_ACTION && wParam == WM_MOUSEWHEEL) {
        MSLLHOOKSTRUCT* p = (MSLLHOOKSTRUCT*)lParam;
        if (AreModifiersActive()) {
            int delta = GET_WHEEL_DELTA_WPARAM(p->mouseData);
            g_targetOffsetX -= (delta * 1.5);
            g_lastInputTime = GetTickCount();
            return 1;
        }
    }
    return CallNextHookEx(NULL, nCode, wParam, lParam);
}
