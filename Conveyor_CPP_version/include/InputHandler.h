#pragma once
#include "Common.h"

class InputHandler {
public:
    static void Start();
    static void Stop();
    static bool AreModifiersActive();
    
    static LRESULT CALLBACK LowLevelKeyboardProc(int nCode, WPARAM wParam, LPARAM lParam);
    static LRESULT CALLBACK LowLevelMouseProc(int nCode, WPARAM wParam, LPARAM lParam);

    static HHOOK hKeyHook;
    static HHOOK hMouseHook;
};
