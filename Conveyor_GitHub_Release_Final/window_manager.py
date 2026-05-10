import window_utils
import win32gui
import win32con

class WindowManager:
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.managed_hwnds = []
        self.window_widths = {}
        self.window_gap = 5
        self.last_pos_cache = {}
        
        self.standard_width_factor = 0.5 # 50% screen width
        self.heavy_width_factor = 0.5    # Also 50% for consistency as requested
        self.floating_hwnds = set()
        self.last_active_hwnd = None

    def refresh_list(self, floating_classes=None, verbose=False):
        self.last_active_hwnd = win32gui.GetForegroundWindow()
        
        # Jika verbose, kita cetak header laporan
        if verbose: print("\n=== STARTING FULL WINDOW SCAN ===", flush=True)
        
        all_real = window_utils.get_managed_windows()
        
        # Filter based on user-toggled floating AND config-defined floating classes
        self.managed_hwnds = []
        for hwnd in all_real:
            cls = win32gui.GetClassName(hwnd)
            if hwnd in self.floating_hwnds: 
                if verbose: print(f"[Skipped] Title: '{win32gui.GetWindowText(hwnd)}', Reason: 'Manually Floating'", flush=True)
                continue
            if floating_classes and cls in floating_classes: 
                if verbose: print(f"[Skipped] Title: '{win32gui.GetWindowText(hwnd)}', Reason: 'Config Floating Class'", flush=True)
                continue
            self.managed_hwnds.append(hwnd)

        if verbose: print(f"=== SCAN FINISHED. Managed: {len(self.managed_hwnds)} windows ===\n", flush=True)

        for hwnd in self.managed_hwnds:
            if hwnd not in self.window_widths:
                factor = self.heavy_width_factor if window_utils.is_heavy_app(hwnd) else self.standard_width_factor
                self.window_widths[hwnd] = int(self.screen_w * factor)

    def toggle_floating(self, hwnd):
        if not hwnd: return False
        if hwnd in self.floating_hwnds:
            self.floating_hwnds.remove(hwnd)
            # Set back to Not Topmost when returning to tiling strip
            win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, 
                                 win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)
        else:
            self.floating_hwnds.add(hwnd)
            # Set to Topmost when floating
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, 
                                 win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)
            if hwnd in self.managed_hwnds:
                self.managed_hwnds.remove(hwnd)
        self.last_pos_cache.clear()
        return True

    def sync_states(self, floating_classes=None):
        """Purely syncs the list. Removal of windows naturally causes the layout to tighten."""
        all_real = window_utils.get_managed_windows()
        
        current_list = []
        for hwnd in all_real:
            cls = win32gui.GetClassName(hwnd)
            
            # Jika ini Game atau Aplikasi Berat, paksa masuk ke barisan tiling
            if window_utils.is_heavy_app(hwnd):
                if hwnd in self.floating_hwnds:
                    self.floating_hwnds.remove(hwnd)
                    # Pastikan status topmost dicabut agar bisa ikut digeser
                    win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, 
                                         win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)
                current_list.append(hwnd)
                continue
                
            if hwnd in self.floating_hwnds: continue
            if floating_classes and any(fc.lower() in cls.lower() for fc in floating_classes): continue
            current_list.append(hwnd)
        
        focused_hwnd = win32gui.GetForegroundWindow()
        
        if current_list == self.managed_hwnds:
            if focused_hwnd in self.managed_hwnds:
                self.last_active_hwnd = focused_hwnd
            return False

        new_windows = [h for h in current_list if h not in self.managed_hwnds]
        removed_windows = [h for h in self.managed_hwnds if h not in current_list]

        # 1. REMOVE
        for h in removed_windows:
            if h in self.managed_hwnds:
                self.managed_hwnds.remove(h)
                if h in self.last_pos_cache: del self.last_pos_cache[h]

        # 2. ADD: Smart Insertion (to the right of last active)
        if new_windows:
            try:
                target_hwnd = self.last_active_hwnd
                if target_hwnd in self.managed_hwnds:
                    idx = self.managed_hwnds.index(target_hwnd)
                    for i, h in enumerate(new_windows):
                        self.managed_hwnds.insert(idx + 1 + i, h)
                else:
                    self.managed_hwnds.extend(new_windows)
            except:
                self.managed_hwnds.extend(new_windows)

        if focused_hwnd in self.managed_hwnds:
            self.last_active_hwnd = focused_hwnd

        for h in new_windows:
            if h not in self.window_widths:
                factor = self.heavy_width_factor if window_utils.is_heavy_app(h) else self.standard_width_factor
                self.window_widths[h] = int(self.screen_w * factor)
                
        # Force cache clear to ensure immediate 'tightening' of the strip
        if removed_windows or new_windows:
            self.last_pos_cache.clear()
            return True
            
        return False

    def get_width(self, hwnd):
        return self.window_widths.get(hwnd, int(self.screen_w * self.standard_width_factor))

    def calculate_layout(self, offset_x):
        """Tightens the layout by iterating through the current list sequentially.
        Optimized with view clipping for performance with 15+ windows.
        """
        layout = []
        current_x = int(-offset_x)
        
        # Buffer of 1 screen width to ensure smooth entry/exit
        buffer = self.screen_w
        
        for hwnd in self.managed_hwnds:
            w = int(self.get_width(hwnd))
            
            # View Clipping: Only update if window is within or near the viewport
            if (current_x + w > -buffer) and (current_x < self.screen_w + buffer):
                target_rect = (current_x, 0, w, self.screen_h)
                if self.last_pos_cache.get(hwnd) != target_rect:
                    layout.append((hwnd, current_x, 0, w, self.screen_h, False))
                    self.last_pos_cache[hwnd] = target_rect
            
            # The next window starts exactly after the current one + gap
            current_x += w + self.window_gap
            
        return layout

    def swap_windows(self, idx1, idx2):
        if 0 <= idx1 < len(self.managed_hwnds) and 0 <= idx2 < len(self.managed_hwnds):
            self.managed_hwnds[idx1], self.managed_hwnds[idx2] = self.managed_hwnds[idx2], self.managed_hwnds[idx1]
            self.last_pos_cache.clear()
            return True
        return False
