import time
import threading
import window_utils
from config_manager import ConfigManager
from window_manager import WindowManager
from input_handler import InputHandler
import tkinter as tk
import os
import ctypes

class HyperscrollApp:
    def __init__(self):
        self.config = ConfigManager()
        w, h = window_utils.get_work_area()
        self.wm = WindowManager(w, h)
        self.input = InputHandler(self)
        
        # Physics & Animation State
        self.current_offset_x = 0.0
        self.target_offset_x = 0.0
        
        self.is_enabled = True
        self.is_recording = False # RESTORED: Required by input_handler.py
        self.running = True
        
        self.lerp_factor = 0.15 
        self.snap_delay = 0.20 
        self.last_input_time = time.time()
        self.is_moving = False
        self.is_snapping = False
        
        self.last_config_mtime = os.path.getmtime(self.config.config_path)
        ctypes.windll.user32.SystemParametersInfoW(0x2001, 0, 0, 0x02)

    def trigger_layout(self):
        if not self.is_enabled: return
        layout = self.wm.calculate_layout(self.current_offset_x)
        if not layout: return
        for hwnd, x, y, w, h, x_only in layout:
            window_utils.set_window_pos(hwnd, x, y, w, h, x_only=x_only)

    def check_config_reload(self):
        try:
            mtime = os.path.getmtime(self.config.config_path)
            if mtime > self.last_config_mtime:
                self.config.config = self.config.load_config()
                self.config.modifier_key = self.config.get_modifier_key()
                self.wm.window_gap = self.config.config.get("window_gap", 5)
                self.last_config_mtime = mtime
        except: pass

    def animation_loop(self):
        last_state_check = time.time()
        while self.running:
            if not self.is_enabled:
                time.sleep(0.5); continue
            
            now = time.time()
            if now - last_state_check > 0.8:
                if self.wm.sync_states():
                    self.trigger_layout()
                self.check_config_reload()
                last_state_check = now

            diff = self.target_offset_x - self.current_offset_x
            if abs(diff) > 0.1:
                self.is_moving = True
                current_lerp = self.lerp_factor
                if abs(diff) < 50: current_lerp *= 0.8
                self.current_offset_x += diff * current_lerp
                self.trigger_layout()
                sleep_time = 0.008 
            else:
                if self.is_moving:
                    self.current_offset_x = self.target_offset_x
                    self.trigger_layout()
                    if not self.input.modifier_pressed:
                        self.focus_central_window()
                    self.is_moving = False
                    self.is_snapping = False
                
                if not self.input.modifier_pressed and not self.is_snapping:
                    if now - self.last_input_time > self.snap_delay:
                        snap_target = self.get_snap_target()
                        if abs(self.target_offset_x - snap_target) > 1.0:
                            self.target_offset_x = snap_target
                            self.is_snapping = True
                
                sleep_time = 0.05

            time.sleep(sleep_time)

    def get_snap_target(self):
        if not self.wm.managed_hwnds: return 0
        acc_x = 0; screen_center = self.wm.screen_w / 2
        min_dist = float('inf'); best_offset = self.target_offset_x
        for hwnd in self.wm.managed_hwnds:
            w = self.wm.get_width(hwnd)
            win_center_world = acc_x + (w / 2)
            dist = abs(self.target_offset_x - win_center_world + screen_center)
            if dist < min_dist:
                min_dist = dist; best_offset = win_center_world - screen_center
            acc_x += w + self.wm.window_gap
        return best_offset

    def focus_central_window(self):
        if not self.wm.managed_hwnds: return
        screen_center = self.wm.screen_w / 2
        min_dist = float('inf'); central_hwnd = None
        curr_x = -self.current_offset_x
        for hwnd in self.wm.managed_hwnds:
            w = self.wm.get_width(hwnd)
            if abs((curr_x + w/2) - screen_center) < min_dist:
                min_dist = abs((curr_x + w/2) - screen_center); central_hwnd = hwnd
            curr_x += w + self.wm.window_gap
        if central_hwnd:
            try:
                import win32gui
                window_utils.stop_flashing(central_hwnd)
                win32gui.SetForegroundWindow(central_hwnd)
            except: pass

    def start(self):
        self.wm.window_gap = self.config.config.get("window_gap", 5)
        self.wm.refresh_list(); self.trigger_layout()
        threading.Thread(target=self.animation_loop, daemon=True).start()
        self.input.start()
        
        root = tk.Tk(); root.title("Conveyor Runner")
        root.geometry("220x80"); root.attributes("-topmost", True)
        tk.Label(root, text="Conveyor is Active", font=("Segoe UI", 10, "bold")).pack(pady=5)
        tk.Label(root, text="Mod: Alt | Edit config live", font=("Segoe UI", 8)).pack()
        root.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))
        root.mainloop()

if __name__ == "__main__":
    app = HyperscrollApp()
    app.start()
