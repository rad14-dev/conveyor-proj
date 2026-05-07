import window_utils
import win32gui

class WindowManager:
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.managed_hwnds = []
        self.window_widths = {}
        self.window_gap = 0
        self.last_pos_cache = {}
        
        self.standard_width_factor = 0.5 
        self.heavy_width_factor = 0.75    

    def refresh_list(self):
        self.managed_hwnds = window_utils.get_managed_windows()
        for hwnd in self.managed_hwnds:
            if hwnd not in self.window_widths:
                factor = self.heavy_width_factor if window_utils.is_heavy_app(hwnd) else self.standard_width_factor
                self.window_widths[hwnd] = int(self.screen_w * factor)

    def sync_states(self):
        """Purely syncs the list. Removal of windows naturally causes the layout to tighten."""
        current_list = window_utils.get_managed_windows()
        if current_list == self.managed_hwnds:
            return False

        new_windows = [h for h in current_list if h not in self.managed_hwnds]
        removed_windows = [h for h in self.managed_hwnds if h not in current_list]

        # 1. REMOVE: Just remove from list. 
        # In the next calculate_layout() call, the next windows will automatically take these coordinates.
        for h in removed_windows:
            if h in self.managed_hwnds:
                self.managed_hwnds.remove(h)
                if h in self.last_pos_cache: del self.last_pos_cache[h]

        # 2. ADD: Smart Insertion
        if new_windows:
            focused_hwnd = win32gui.GetForegroundWindow()
            try:
                if focused_hwnd in self.managed_hwnds:
                    idx = self.managed_hwnds.index(focused_hwnd)
                    for i, h in enumerate(new_windows):
                        self.managed_hwnds.insert(idx + 1 + i, h)
                else:
                    self.managed_hwnds.extend(new_windows)
            except:
                self.managed_hwnds.extend(new_windows)

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
        """Tightens the layout by iterating through the current list sequentially."""
        layout = []
        current_x = int(-offset_x)
        
        for hwnd in self.managed_hwnds:
            w = int(self.get_width(hwnd))
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
