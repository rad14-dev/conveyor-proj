import time
import ctypes
from pynput import keyboard, mouse
import win32gui

class InputHandler:
    def __init__(self, app_core):
        self.app = app_core
        self.active_modifiers = set()
        self.dragging_hwnd = None
        self.resizing_hwnd = None
        self.resize_edge = None
        self.last_mouse_x = 0
        
        self.mouse_listener = mouse.Listener(
            win32_event_filter=self.win32_event_filter,
            on_scroll=self.on_scroll,
            on_click=self.on_click,
            on_move=self.on_move
        )
        self.key_listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )

    def start(self):
        self.mouse_listener.start()
        self.key_listener.start()

    def stop(self):
        self.mouse_listener.stop()
        self.key_listener.stop()

    def are_modifiers_active(self):
        required = self.app.config.modifier_keys
        return all(mod in self.active_modifiers for mod in required)

    def win32_event_filter(self, msg, data):
        if not self.app.is_enabled or self.app.is_recording: return True
        if (msg == 0x020A or msg == 0x020E) and self.are_modifiers_active():
            delta = ctypes.c_short(data.mouseData >> 16).value
            dx = delta / 120.0 if msg == 0x020E else 0
            dy = delta / 120.0 if msg == 0x020A else 0
            self.on_scroll(data.pt.x, data.pt.y, dx, dy)
            if hasattr(self.mouse_listener, 'suppress_event'): self.mouse_listener.suppress_event()
            return False 
        return True

    def on_scroll(self, x, y, dx, dy):
        if self.app.is_enabled and self.are_modifiers_active():
            self.app.last_input_time = time.time()
            scroll_amount = dy * 120.0 
            self.app.target_offset_x += scroll_amount
            
            # Reset snapping agar tidak mengganggu gerakan
            self.app.is_snapping = False

    def on_click(self, x, y, button, pressed):
        if pressed and self.are_modifiers_active():
            active = win32gui.GetForegroundWindow()
            if active in self.app.wm.managed_hwnds:
                idx = self.app.wm.managed_hwnds.index(active)
                acc_x = 0
                for i in range(idx):
                    acc_x += self.app.wm.get_width(self.app.wm.managed_hwnds[i]) + self.app.wm.window_gap
                
                win_x_on_screen = acc_x - self.app.current_offset_x
                win_w = self.app.wm.get_width(active)
                
                edge_margin = 35
                if abs(x - win_x_on_screen) < edge_margin:
                    self.resizing_hwnd, self.resize_edge = active, 'left'
                elif abs(x - (win_x_on_screen + win_w)) < edge_margin:
                    self.resizing_hwnd, self.resize_edge = active, 'right'
                else:
                    self.dragging_hwnd = active
                self.last_mouse_x = x
        else:
            self.dragging_hwnd = self.resizing_hwnd = None

    def on_move(self, x, y):
        if not self.are_modifiers_active(): return
        if self.resizing_hwnd:
            dx = x - self.last_mouse_x
            curr_w = self.app.wm.window_widths.get(self.resizing_hwnd, self.app.wm.screen_w)
            if self.resize_edge == 'right':
                self.app.wm.window_widths[self.resizing_hwnd] = max(200, curr_w + dx)
            else:
                new_w = max(200, curr_w - dx)
                self.app.wm.window_widths[self.resizing_hwnd] = new_w
                self.app.current_offset_x += (curr_w - new_w)
                self.app.target_offset_x = self.app.current_offset_x
            self.last_mouse_x = x
            self.app.trigger_layout(); return
        if self.dragging_hwnd:
            cursor_world_x = x + self.app.current_offset_x
            acc_x = 0
            try:
                idx = self.app.wm.managed_hwnds.index(self.dragging_hwnd)
                for i, hwnd in enumerate(self.app.wm.managed_hwnds):
                    w = self.app.wm.get_width(hwnd)
                    if i != idx:
                        if abs(cursor_world_x - (acc_x + w/2)) < 60:
                            if self.app.wm.swap_windows(idx, i): self.app.trigger_layout(); break
                    acc_x += w + self.app.wm.window_gap
            except: pass

    def on_press(self, key):
        if self.app.is_recording: return False
        if not self.app.is_enabled: return
        
        if key in self.app.config.modifier_keys:
            self.active_modifiers.add(key)
            
        try:
            active = win32gui.GetForegroundWindow()
            curr_key = key.char.lower() if hasattr(key, 'char') and key.char else str(key).replace("Key.", "").lower()
            shortcuts = self.app.config.shortcuts
            
            # --- PRIORITAS: Alt Only (Resize & Refresh) ---
            is_alt_pressed = (keyboard.Key.alt_l in self.active_modifiers) or (keyboard.Key.alt_r in self.active_modifiers)
            if is_alt_pressed:
                # Shortcut Refresh: Alt + Q
                if curr_key == "q":
                    self.app.wm.last_pos_cache.clear()
                    floating_classes = self.app.config.config.get("floating_classes", [])
                    self.app.wm.refresh_list(floating_classes, verbose=True)
                    self.app.pending_sync = True
                    return
                
                # Shortcut Resize: Alt + 1,2,3,4
                if active in self.app.wm.managed_hwnds:
                    resize_map = {"1": 0.25, "2": 0.5, "3": 0.75, "4": 1.0}
                    if curr_key in resize_map:
                        self.app.wm.window_widths[active] = int(self.app.wm.screen_w * resize_map[curr_key])
                        self.app.trigger_layout()
                        return

            # --- SHORTCUTS LAIN (Win + Alt) ---
            if self.are_modifiers_active():
                # Floating toggle
                if curr_key == shortcuts.get("toggle_floating"):
                    if self.app.wm.toggle_floating(active):
                        self.app.trigger_layout()
                    return

                if active in self.app.wm.managed_hwnds:
                    idx = self.app.wm.managed_hwnds.index(active)
                    if curr_key == shortcuts.get("swap_right"):
                        if self.app.wm.swap_windows(idx, idx+1): self.app.trigger_layout()
                    elif curr_key == shortcuts.get("swap_left"):
                        if self.app.wm.swap_windows(idx, idx-1): self.app.trigger_layout()
                    elif curr_key == shortcuts.get("nav_left"):
                        self.app.last_input_time = time.time()
                        self.app.target_offset_x -= 300
                    elif curr_key == shortcuts.get("nav_right"):
                        self.app.last_input_time = time.time()
                        self.app.target_offset_x += 300
        except: pass

    def on_release(self, key):
        if key in self.active_modifiers:
            self.active_modifiers.remove(key)
            if not self.active_modifiers: # All modifiers released
                # Set last_input_time to the past to trigger immediate snap
                self.app.last_input_time = time.time() - self.app.snap_delay - 1.0
