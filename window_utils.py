import win32gui
import win32con
import ctypes
import ctypes.wintypes

# Force strict DPI awareness for pixel-perfect stability
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    ctypes.windll.user32.SetProcessDPIAware()

ctypes.windll.user32.AllowSetForegroundWindow(-1)

def get_work_area():
    rect = ctypes.wintypes.RECT()
    ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(rect), 0)
    return rect.right - rect.left, rect.bottom - rect.top

def is_cloaked(hwnd):
    val = ctypes.c_int(0)
    res = ctypes.windll.dwmapi.DwmGetWindowAttribute(hwnd, 14, ctypes.byref(val), 4)
    return val.value != 0 if res == 0 else False

def is_heavy_app(hwnd):
    try:
        title = win32gui.GetWindowText(hwnd).lower()
        cls = win32gui.GetClassName(hwnd).lower()
        heavy = ["affinity", "photoshop", "illustrator", "premiere", "blender", "figma"]
        return any(k in title or k in cls for k in heavy)
    except: return False

def is_real_window(hwnd):
    if not win32gui.IsWindowVisible(hwnd): return False
    if is_cloaked(hwnd): return False
    title = win32gui.GetWindowText(hwnd)
    if not title or "Conveyor" in title: return False
    
    cls = win32gui.GetClassName(hwnd)
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    if ex_style & win32con.WS_EX_TOOLWINDOW: return False
    
    blocked_classes = ['Shell_TrayWnd', 'Progman', 'WorkerW', 'Windows.UI.Core.CoreWindow']
    if cls in blocked_classes: return False
    
    blocked_titles = ['Start', 'Search', 'Task View']
    if title in blocked_titles: return False
    return True

def get_managed_windows():
    windows = []
    def callback(hwnd, _):
        if is_real_window(hwnd): windows.append(hwnd)
    win32gui.EnumWindows(callback, None)
    return windows

def set_window_pos(hwnd, x, y, w, h, x_only=False):
    """Applying positions with flags that prioritize layout stability."""
    # SWP_NOCOPYBITS: Prevents Windows from trying to be smart about redrawing, reducing jitter.
    # SWP_NOOWNERZORDER: Ensures we don't mess with window stacking, which can cause 'jumping'.
    flags = win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE | win32con.SWP_ASYNCWINDOWPOS | \
            win32con.SWP_SHOWWINDOW | win32con.SWP_NOCOPYBITS | win32con.SWP_NOOWNERZORDER
            
    if x_only: flags |= win32con.SWP_NOSIZE
    else: flags |= win32con.SWP_FRAMECHANGED
    
    try:
        # Use integer casts to ensure pixel-perfect placement
        win32gui.SetWindowPos(hwnd, 0, int(x), int(y), int(w), int(h), flags)
    except: pass

def stop_flashing(hwnd):
    try: ctypes.windll.user32.FlashWindow(hwnd, 0)
    except: pass
