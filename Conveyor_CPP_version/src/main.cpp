#include "../include/Common.h"
#include "../include/WindowManager.h"
#include "../include/InputHandler.h"
#include "../include/Utils.h"

// Global State
WindowManager g_wm;
Config g_config;
double g_targetOffsetX = 0.0;
double g_currentOffsetX = 0.0;
double g_startOffsetX = 0.0;
double g_animProgress = 1.0;
double g_animDuration = 0.4;
DWORD g_lastInputTime = 0;
bool g_pendingSync = false;
bool g_running = true;
NOTIFYICONDATAA g_nid = {0};

void TriggerLayout() {
    RECT wa = Utils::GetWorkArea();
    int sw = wa.right - wa.left;
    int sh = wa.bottom - wa.top;
    g_wm.UpdateLayout(sw, sh, wa.top, sh, g_currentOffsetX, g_config.windowGap);
}

double GetSnapTarget() {
    if (g_wm.managedHwnds.empty()) return 0;
    
    RECT wa = Utils::GetWorkArea();
    int sw = wa.right - wa.left;
    
    std::vector<double> candidates;
    int acc_x = 0;
    for (HWND hwnd : g_wm.managedHwnds) {
        int w = g_wm.windowWidths[hwnd];
        candidates.push_back(acc_x + (w / 2.0) - (sw / 2.0));
        candidates.push_back((double)acc_x);
        candidates.push_back((double)(acc_x + w - sw));
        acc_x += w + g_config.windowGap;
    }
    
    double best = g_targetOffsetX;
    double minDist = 1e9;
    for (double c : candidates) {
        double d = std::abs(c - g_targetOffsetX);
        if (d < minDist) { minDist = d; best = c; }
    }
    return best;
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
            g_running = false;
            PostQuitMessage(0);
        }
    } else if (msg == WM_DESTROY) {
        PostQuitMessage(0);
    }
    return DefWindowProc(hwnd, msg, wParam, lParam);
}

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    SetProcessDPIAware();
    
    WNDCLASSA wc = {0};
    wc.lpfnWndProc = WndProc;
    wc.hInstance = hInstance;
    wc.lpszClassName = "ConveyorCPPClass";
    RegisterClassA(&wc);
    HWND hHiddenWnd = CreateWindowA(wc.lpszClassName, "Conveyor Service", 0, 0, 0, 0, 0, NULL, NULL, hInstance, NULL);

    g_nid.cbSize = sizeof(NOTIFYICONDATAA);
    g_nid.hWnd = hHiddenWnd;
    g_nid.uID = 1;
    g_nid.uFlags = NIF_ICON | NIF_MESSAGE | NIF_TIP;
    g_nid.uCallbackMessage = WM_TRAYICON;
    g_nid.hIcon = LoadIcon(NULL, IDI_APPLICATION);
    strcpy(g_nid.szTip, "Conveyor CPP Port");
    Shell_NotifyIconA(NIM_ADD, &g_nid);

    g_wm.RefreshList(g_config);
    InputHandler::Start();

    auto lastTime = std::chrono::high_resolution_clock::now();
    double prevTarget = g_targetOffsetX;

    MSG msg;
    while (g_running) {
        while (PeekMessage(&msg, NULL, 0, 0, PM_REMOVE)) {
            TranslateMessage(&msg);
            DispatchMessage(&msg);
        }

        auto now = std::chrono::high_resolution_clock::now();
        std::chrono::duration<double> elapsed = now - lastTime;
        double dt = elapsed.count();
        lastTime = now;

        static double lastSyncCheck = 0;
        lastSyncCheck += dt;
        if (g_pendingSync || lastSyncCheck > 2.0) {
            if (g_wm.SyncStates(g_config)) {
                TriggerLayout();
            }
            g_pendingSync = false;
            lastSyncCheck = 0;
        }

        if (prevTarget != g_targetOffsetX) {
            g_startOffsetX = g_currentOffsetX;
            g_animProgress = 0.0;
            prevTarget = g_targetOffsetX;
        }

        if (g_animProgress < 1.0) {
            g_animProgress += dt / g_animDuration;
            if (g_animProgress > 1.0) g_animProgress = 1.0;
            
            double easedT = Utils::EaseOutCubic(g_animProgress);
            g_currentOffsetX = g_startOffsetX + (g_targetOffsetX - g_startOffsetX) * easedT;
            TriggerLayout();
        } else {
            if (!InputHandler::AreModifiersActive()) {
                DWORD tick = GetTickCount();
                if (tick - g_lastInputTime > 150) {
                    double snap = GetSnapTarget();
                    if (std::abs(g_targetOffsetX - snap) > 1.0) {
                        g_targetOffsetX = snap;
                    }
                }
            }
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(8));
    }

    InputHandler::Stop();
    Shell_NotifyIconA(NIM_DELETE, &g_nid);
    return 0;
}
