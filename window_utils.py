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
    title = win32gui.GetWindowText(hwnd)
    cls = win32gui.GetClassName(hwnd)
    
    # --- LOGIKA KHUSUS CHROME ---
    # Jika ini Chrome dan punya judul, kita sangat permisif agar tidak hilang saat navigasi
    is_chrome = (cls == "Chrome_WidgetWin_1")
    
    if not win32gui.IsWindowVisible(hwnd): 
        return False
        
    if win32gui.IsIconic(hwnd): 
        return False
    
    if is_cloaked(hwnd) and not (is_chrome and title): 
        return False
    
    # Abaikan jendela yang punya "Owner", kecuali Chrome yang punya judul
    if win32gui.GetWindow(hwnd, win32con.GW_OWNER) != 0: 
        if not (is_chrome and title):
            return False
    
    if not title:
        return False
        
    if title == "Conveyor Runner": return False
    
    style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    
    # Filter ToolWindows (jendela kecil/overlay)
    if ex_style & win32con.WS_EX_TOOLWINDOW: 
        return False
    
    # Hanya abaikan jendela POPUP yang tidak memiliki border tebal (biasanya menu klik kanan/tooltip)
    if (style & win32con.WS_POPUP) and not (style & win32con.WS_THICKFRAME):
        return False
    
    blocked_classes = [
        'Shell_TrayWnd', 'Progman', 'WorkerW', 
        'Windows.UI.Core.CoreWindow', 'SearchUI.exe', 'GhostWnd'
    ]
    if cls in blocked_classes: 
        return False
    
    blocked_titles = ['Start', 'Search', 'Task View']
    if title in blocked_titles: 
        return False
    
    return True

def get_managed_windows():
    windows = []
    def callback(hwnd, _):
        if is_real_window(hwnd): windows.append(hwnd)
    win32gui.EnumWindows(callback, None)
    return windows

def set_window_pos(hwnd, x, y, w, h, x_only=False):
    """Applying positions with optimized Z-order management to prevent overlapping."""
    try:
        flags = win32con.SWP_NOACTIVATE | win32con.SWP_ASYNCWINDOWPOS | \
                win32con.SWP_SHOWWINDOW | win32con.SWP_NOCOPYBITS
                
        if x_only: flags |= win32con.SWP_NOSIZE
        else: flags |= win32con.SWP_FRAMECHANGED
        
        # Combined call for efficiency
        win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, int(x), int(y), int(w), int(h), flags)
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)
    except: pass

def stop_flashing(hwnd):
    try: ctypes.windll.user32.FlashWindow(hwnd, 0)
    except: pass

# WinEventHook constants
EVENT_OBJECT_DESTROY = 0x8001
EVENT_OBJECT_SHOW = 0x8002
EVENT_OBJECT_HIDE = 0x8003
EVENT_SYSTEM_MINIMIZESTART = 0x0016
EVENT_SYSTEM_MINIMIZEEND = 0x0017
EVENT_SYSTEM_FOREGROUND = 0x0003
WINEVENT_OUTOFCONTEXT = 0x0000

def set_win_event_hook(callback_func):
    """Sets a hook to listen for window changes globally."""
    WINEVENTPROC = ctypes.WINFUNCTYPE(None, ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD, ctypes.wintypes.HWND, 
                                     ctypes.wintypes.LONG, ctypes.wintypes.LONG, ctypes.wintypes.DWORD, ctypes.wintypes.DWORD)
    
    # Keep a reference to the callback to prevent GC
    setattr(set_win_event_hook, '_callback', WINEVENTPROC(callback_func))
    
    return ctypes.windll.user32.SetWinEventHook(
        EVENT_SYSTEM_MINIMIZESTART, EVENT_OBJECT_HIDE, # Range of events
        0, getattr(set_win_event_hook, '_callback'), 0, 0, WINEVENT_OUTOFCONTEXT
    )
