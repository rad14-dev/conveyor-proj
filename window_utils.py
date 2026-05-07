import win32gui
import win32con
import ctypes
from screeninfo import get_monitors

# Ensure accurate Windows coordinates (DPI Awareness)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    ctypes.windll.user32.SetProcessDPIAware()

DWMWA_CLOAKED = 14
DwmGetWindowAttribute = ctypes.windll.dwmapi.DwmGetWindowAttribute

def is_cloaked(hwnd):
    """Checks if a window is 'cloaked', meaning it's on another Virtual Desktop or hidden by Windows."""
    is_cloaked_val = ctypes.c_int(0)
    res = DwmGetWindowAttribute(hwnd, DWMWA_CLOAKED, ctypes.byref(is_cloaked_val), ctypes.sizeof(is_cloaked_val))
    if res == 0:
        return is_cloaked_val.value != 0
    return False

def get_screen_size():
    monitor = get_monitors()[0]
    return monitor.width, monitor.height

def is_real_window(hwnd):
    """Filter to ensure it's an application window, including UWP (Settings, etc)."""
    if not win32gui.IsWindowVisible(hwnd):
        return False
        
    # Skip windows on other virtual desktops!
    if is_cloaked(hwnd):
        return False
        
    # Skip tooltips, overlays, and floating palettes
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    if ex_style & win32con.WS_EX_TOOLWINDOW:
        return False
        
    title = win32gui.GetWindowText(hwnd)
    if not title:
        return False
    
    clsname = win32gui.GetClassName(hwnd)
    
    blocked_classes = [
        'Shell_TrayWnd',      
        'Shell_SecondaryTrayWnd', 
        'Progman',            
        'WorkerW',            
        'Windows.UI.Core.CoreWindow', 
    ]
    
    if clsname in blocked_classes:
        return False
        
    blocked_titles = ['Start', 'Search', 'Program Manager', 'Task View', 'Conveyor Settings']
    if title in blocked_titles:
        return False
        
    return True

def get_managed_windows():
    windows = []
    def callback(hwnd, extra):
        if is_real_window(hwnd):
            windows.append(hwnd)
    win32gui.EnumWindows(callback, None)
    return windows

def set_window_pos(hwnd, x, y, w, h):
    """Force window to specific coordinates with high priority."""
    win32gui.SetWindowPos(
        hwnd, 0, 
        int(x), int(y), int(w), int(h), 
        win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE | win32con.SWP_ASYNCWINDOWPOS | win32con.SWP_SHOWWINDOW | win32con.SWP_FRAMECHANGED
    )
