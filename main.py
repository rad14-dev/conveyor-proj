import time
import threading
import win32gui
from pynput import keyboard, mouse
import window_utils

class HyperscrollApp:
    def __init__(self):
        self.screen_w, self.screen_h = window_utils.get_screen_size()
        
        # Positions
        self.current_offset_x = 0.0
        self.target_offset_x = 0.0
        
        # State
        self.managed_hwnds = []
        self.window_widths = {}      
        self.running = True
        self.modifier_pressed = False
        
        # Animation & Snapping
        self.lerp_factor = 0.15
        self.scroll_sensitivity = 1.0
        self.last_input_time = time.time()
        self.snap_delay = 0.6        
        self.is_moving = False
        
        # Layout Spacing
        self.window_gap = 5
        self.last_state_check = time.time()
        self.last_res_check = time.time()
        self.hot_zone_margin = 15 

    def get_width(self, hwnd):
        # Always calculate percentage-based width to remain responsive to resolution changes
        # If no custom width, default to 70% of CURRENT screen width
        return self.window_widths.get(hwnd, int(self.screen_w * 0.7))

    def refresh(self):
        self.managed_hwnds = window_utils.get_managed_windows()
        valid_hwnds = set(self.managed_hwnds)
        self.window_widths = {h: w for h, w in self.window_widths.items() if h in valid_hwnds}

    def apply_layout(self):
        cursor_x = -self.current_offset_x
        for hwnd in self.managed_hwnds:
            w = self.get_width(hwnd)
            buffer = 300
            if cursor_x > self.screen_w + buffer or (cursor_x + w) < -buffer:
                cursor_x += w
                continue
                
            draw_w = w - self.window_gap
            draw_x = cursor_x + (self.window_gap // 2)
            # Re-scale height to current screen_h automatically
            window_utils.set_window_pos(hwnd, draw_x, 0, draw_w, self.screen_h)
            cursor_x += w

    def check_resolution(self):
        """Detect changes in screen resolution or orientation."""
        new_w, new_h = window_utils.get_screen_size()
        if new_w != self.screen_w or new_h != self.screen_h:
            print(f"[Log] Display changed: {new_w}x{new_h}. Adapting layout...")
            self.screen_w = new_w
            self.screen_h = new_h
            # We don't clear window_widths, but we should probably scale them 
            # for now, apply_layout will handle the height automatically.
            self.apply_layout()

    def check_window_states(self):
        current_system_visible = window_utils.get_managed_windows()
        changed = False
        
        for hwnd in current_system_visible:
            if hwnd not in self.managed_hwnds:
                print(f"[Log] New window captured: {hwnd}.")
                self.managed_hwnds.append(hwnd)
                self.apply_layout()
                changed = True
        
        still_valid = []
        for hwnd in self.managed_hwnds:
            if win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd) and not win32gui.IsIconic(hwnd):
                still_valid.append(hwnd)
                try:
                    rect = win32gui.GetWindowRect(hwnd)
                    actual_w = rect[2] - rect[0]
                    if abs(actual_w - (self.get_width(hwnd) - self.window_gap)) > 15:
                        self.window_widths[hwnd] = actual_w + self.window_gap
                        changed = True
                except Exception: pass
            else:
                changed = True
        
        if changed:
            self.managed_hwnds = still_valid
            self.apply_layout()

    def get_snap_target(self):
        if not self.managed_hwnds: return 0
        best_offset = self.target_offset_x
        min_dist = float('inf')
        current_win_x = 0
        screen_center = self.screen_w / 2
        for hwnd in self.managed_hwnds:
            w = self.get_width(hwnd)
            win_center_in_world = current_win_x + (w / 2)
            potential_offset = win_center_in_world - screen_center
            dist = abs(self.target_offset_x - potential_offset)
            if dist < min_dist:
                min_dist = dist
                best_offset = potential_offset
            current_win_x += w
        return best_offset

    def animation_loop(self):
        while self.running:
            now = time.time()
            self.handle_hot_zones()
            
            # Check for resolution/orientation changes (every 1s)
            if now - self.last_res_check > 1.0:
                self.check_resolution()
                self.last_res_check = now

            if now - self.last_state_check > 0.15:
                self.check_window_states()
                self.last_state_check = now

            diff = self.target_offset_x - self.current_offset_x
            if abs(diff) > 0.1:
                self.is_moving = True
                self.current_offset_x += diff * self.lerp_factor
                self.apply_layout()
            else:
                if self.is_moving:
                    self.current_offset_x = self.target_offset_x
                    self.apply_layout()
                    self.is_moving = False

            if not self.modifier_pressed and not self.is_moving:
                if now - self.last_input_time > self.snap_delay:
                    snap_target = self.get_snap_target()
                    if abs(self.target_offset_x - snap_target) > 1:
                        self.target_offset_x = snap_target
            time.sleep(0.01)

    def handle_hot_zones(self):
        if not self.modifier_pressed: return
        try:
            x, y = win32gui.GetCursorPos()
            active_hwnd = win32gui.GetForegroundWindow()
            if active_hwnd in self.managed_hwnds:
                new_w = None
                if y < self.hot_zone_margin:
                    new_w = int(self.screen_w * 0.75)
                elif x < self.hot_zone_margin or x > self.screen_w - self.hot_zone_margin:
                    new_w = int(self.screen_w * 0.5)
                elif y > self.screen_h - self.hot_zone_margin:
                    new_w = int(self.screen_w * 0.25)
                
                if new_w and new_w != self.get_width(active_hwnd):
                    self.window_widths[active_hwnd] = new_w
                    self.apply_layout()
        except Exception: pass

    def on_scroll(self, x, y, dx, dy):
        if self.modifier_pressed:
            self.last_input_time = time.time()
            norm_dx = dx * 0.1
            norm_dy = dy * 1.0
            move_delta = norm_dx if abs(norm_dx) > abs(norm_dy) else norm_dy
            move_delta = max(min(move_delta, 1.2), -1.2)
            self.target_offset_x -= (move_delta * 300 * self.scroll_sensitivity)

    def on_press(self, key):
        self.last_input_time = time.time()
        if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            self.modifier_pressed = True
        try:
            active_hwnd = win32gui.GetForegroundWindow()
            if self.modifier_pressed and active_hwnd in self.managed_hwnds:
                if hasattr(key, 'char'):
                    if key.char == '1': 
                        self.window_widths[active_hwnd] = int(self.screen_w * 0.25)
                        self.apply_layout()
                    elif key.char == '2': 
                        self.window_widths[active_hwnd] = int(self.screen_w * 0.5)
                        self.apply_layout()
                    elif key.char == '3': 
                        self.window_widths[active_hwnd] = int(self.screen_w * 0.75)
                        self.apply_layout()

            if key == keyboard.Key.right:
                self.target_offset_x += 400
            elif key == keyboard.Key.left:
                self.target_offset_x -= 400
            elif key == keyboard.Key.esc:
                self.running = False
                return False 
        except Exception: pass

    def on_release(self, key):
        if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            self.modifier_pressed = False
            self.last_input_time = time.time() - self.snap_delay + 0.1

    def start(self):
        print("--- Hyperscroll Fase 4: Responsive Layout ---")
        print("Feature: Automatically adapts to resolution and orientation changes.")
        self.refresh()
        self.apply_layout()
        threading.Thread(target=self.animation_loop, daemon=True).start()
        with mouse.Listener(on_scroll=self.on_scroll) as m_listener:
            with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as k_listener:
                k_listener.join()
            m_listener.stop()

if __name__ == "__main__":
    app = HyperscrollApp()
    app.start()
