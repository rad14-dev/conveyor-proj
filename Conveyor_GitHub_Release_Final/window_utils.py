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
        
        # Check by keywords
        heavy_titles = ['visual studio', 'photoshop', 'premiere', 'chrome', 'edge', 'code', 'zenless', 'honkai', 'genshin', 'star rail', 'zzz', 'hsr']
        if any(k in title or k in cls for k in heavy_titles):
            return True
            
        # Check by physical size (Aggressive detection for Games)
        rect = win32gui.GetWindowRect(hwnd)
        w = rect[2] - rect[0]
        h = rect[3] - rect[1]
        if w > 800 and h > 600:
            return True
            
        return False
    except: return False

def is_real_window(hwnd):
    title = win32gui.GetWindowText(hwnd)
    cls = win32gui.GetClassName(hwnd)
    
    # --- DETEKSI AGRESIF UNTUK GAME & APLIKASI BESAR ---
    is_chrome = (cls == "Chrome_WidgetWin_1")
    try:
        rect = win32gui.GetWindowRect(hwnd)
        w_width = rect[2] - rect[0]
        w_height = rect[3] - rect[1]
    except:
        w_width, w_height = 0, 0

    # Jika jendela sangat besar (seperti 1920x1080), kemungkinan besar itu adalah Game
    # NOTE: Jika aplikasi tidak di-run sebagai ADMIN, GetWindowRect mungkin gagal (0,0)
    is_large = (w_width > 400 and w_height > 400)
    
    # Kata kunci mesin game dan judul populer
    game_keywords = ["zenless", "honkai", "genshin", "star rail", "unity", "unreal", "game", "zzz", "hsr", " Hoyoverse"]
    is_game = any(k in title.lower() or k in cls.lower() for k in game_keywords) or is_large
    
    if not win32gui.IsWindowVisible(hwnd): 
        return False
        
    if win32gui.IsIconic(hwnd): 
        return False
    
    # Cloaked check: Sangat longgar untuk Game/Aplikasi besar
    if is_cloaked(hwnd) and not is_game: 
        return False
    
    # Owner check: Izinkan game meskipun punya owner (beberapa launcher game bekerja begini)
    if win32gui.GetWindow(hwnd, win32con.GW_OWNER) != 0: 
        if not (is_chrome and title) and not is_game:
            return False
    
    if not title:
        return False
        
    if title == "Conveyor Runner": return False
    
    style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    
    # Filter ToolWindows (overlay kecil tetap dibuang)
    if ex_style & win32con.WS_EX_TOOLWINDOW: 
        return False
    
    # --- PENYIMPANGAN UNTUK GAME ---
    # Biasanya kita buang WS_POPUP, tapi untuk Game (atau jendela besar), kita IZINKAN.
    if (style & win32con.WS_POPUP) and not (style & win32con.WS_THICKFRAME):
        if not is_game:
            return False
    
    # Daftar blokir kelas sistem tetap dipertahankan agar tidak mengacaukan Windows
    blocked_classes = [
        'Shell_TrayWnd', 'Progman', 'WorkerW', 
        'Windows.UI.Core.CoreWindow', 'SearchUI.exe', 'GhostWnd', 'ApplicationFrameWindow'
    ]
    if cls in blocked_classes and not is_large: 
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

def batch_set_window_pos(layout_list):
    """
    Applies multiple window positions in a single atomic batch.
    This eliminates 'gaps' and 'lag' between windows during scrolling.
    """
    if not layout_list: return
    
    # Begin a batch for the number of windows we want to move
    count = len(layout_list)
    hdwp = ctypes.windll.user32.BeginDeferWindowPos(count)
    if not hdwp: return
    
    for hwnd, x, y, w, h, x_only in layout_list:
        # SWP_NOZORDER: Don't change Z-order for speed
        # SWP_NOACTIVATE: Don't steal focus
        # SWP_NOCOPYBITS: Reduces redraw artifacts during fast movement
        # IMPORTANT: No SWP_ASYNCWINDOWPOS here for perfect sync
        flags = win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER | \
                win32con.SWP_SHOWWINDOW | win32con.SWP_NOCOPYBITS
                
        if x_only: flags |= win32con.SWP_NOSIZE
        else: flags |= win32con.SWP_FRAMECHANGED
        
        hdwp = ctypes.windll.user32.DeferWindowPos(
            hdwp, hwnd, 0, int(x), int(y), int(w), int(h), flags
        )
        if not hdwp: break
        
    if hdwp:
        # This call executes all the moves at once
        ctypes.windll.user32.EndDeferWindowPos(hdwp)

def set_window_pos(hwnd, x, y, w, h, x_only=False):
    """Applying positions for single window (Fallback)."""
    try:
        flags = win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER | \
                win32con.SWP_SHOWWINDOW | win32con.SWP_NOCOPYBITS
                
        if x_only: flags |= win32con.SWP_NOSIZE
        else: flags |= win32con.SWP_FRAMECHANGED
        
        win32gui.SetWindowPos(hwnd, 0, int(x), int(y), int(w), int(h), flags)
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
