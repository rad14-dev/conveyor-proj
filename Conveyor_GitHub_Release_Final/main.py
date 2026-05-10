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
        
        # Animation & Bezier State
        self.current_offset_x = 0.0
        self.target_offset_x = 0.0
        self.start_offset_x = 0.0
        self.anim_progress = 1.0  # 1.0 means finished
        self.anim_duration = 0.4  # Seconds
        self.last_anim_time = time.time()
        
        self.is_enabled = True
        self.is_recording = False
        self.running = True
        self.snap_delay = 0.1
        self.last_input_time = time.time()
        self.pending_sync = False
        
        self.last_config_mtime = os.path.getmtime(self.config.config_path)
        ctypes.windll.user32.SystemParametersInfoW(0x2001, 0, 0, 0x02)
        
        # Set up instant window detection hook
        self.hook = window_utils.set_win_event_hook(self.on_window_event)

    def ease_out_back(self, x):
        """Smooth Ease Out Back for a premium overshoot effect."""
        c1 = 0.5  # Subtle overshoot (lower = smoother)
        c3 = c1 + 1
        return 1 + c3 * pow(x - 1, 3) + c1 * pow(x - 1, 2)

    def on_window_event(self, hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
        if idObject == 0: 
            self.pending_sync = True

    def trigger_layout(self):
        if not self.is_enabled: return
        layout = self.wm.calculate_layout(self.current_offset_x)
        if layout:
            window_utils.batch_set_window_pos(layout)

    def check_config_reload(self):
        try:
            mtime = os.path.getmtime(self.config.config_path)
            if mtime > self.last_config_mtime:
                self.config.config = self.config.load_config()
                self.config.modifier_keys = self.config.get_modifier_keys()
                self.wm.window_gap = self.config.config.get("window_gap", 5)
                self.last_config_mtime = mtime
        except: pass

    def animation_loop(self):
        last_state_check = time.time()
        while self.running:
            if not self.is_enabled:
                time.sleep(1.0); continue
            
            now = time.time()
            dt = now - self.last_anim_time
            self.last_anim_time = now
            
            if self.pending_sync or (now - last_state_check > 2.0):
                floating_classes = self.config.config.get("floating_classes", [])
                if self.wm.sync_states(floating_classes):
                    self.trigger_layout()
                self.check_config_reload()
                self.pending_sync = False
                last_state_check = now

            # Check for target change
            if hasattr(self, '_prev_target') and self._prev_target != self.target_offset_x:
                self.start_offset_x = self.current_offset_x
                self.anim_progress = 0.0
            self._prev_target = self.target_offset_x

            # --- BEZIER ANIMATION PROGRESS ---
            if self.anim_progress < 1.0:
                self.anim_progress += dt / self.anim_duration
                if self.anim_progress > 1.0: self.anim_progress = 1.0
                
                # Apply Ease Out Back (Overshoot)
                eased_t = self.ease_out_back(self.anim_progress)
                self.current_offset_x = self.start_offset_x + (self.target_offset_x - self.start_offset_x) * eased_t
                
                self.trigger_layout()
                sleep_time = 0.01 # Balanced refresh for better consistency
            else:
                # Idle state / Snapping logic
                if not self.input.are_modifiers_active():
                    if now - self.last_input_time > self.snap_delay:
                        snap_target = self.get_snap_target()
                        if abs(self.target_offset_x - snap_target) > 1.0:
                            self.target_offset_x = snap_target
                            # Focus transition would happen here after snap
                
                sleep_time = 0.015 if self.input.are_modifiers_active() else 0.05

            time.sleep(sleep_time)

    def get_snap_target(self):
        if not self.wm.managed_hwnds: return 0
        
        candidates = []
        acc_x = 0
        sw = self.wm.screen_w
        
        for hwnd in self.wm.managed_hwnds:
            w = self.wm.get_width(hwnd)
            
            # Snap Point 1: Center this window on screen
            candidates.append(acc_x + (w / 2) - (sw / 2))
            
            # Snap Point 2: Align Left edge of this window with Left edge of screen
            candidates.append(float(acc_x))
            
            # Snap Point 3: Align Right edge of this window with Right edge of screen
            candidates.append(float(acc_x + w - sw))
            
            acc_x += w + self.wm.window_gap
            
        if not candidates: return 0
        
        # Pick the candidate closest to the current target_offset_x
        best_offset = min(candidates, key=lambda c: abs(c - self.target_offset_x))
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
        floating_classes = self.config.config.get("floating_classes", [])
        self.wm.refresh_list(floating_classes); self.trigger_layout()
        threading.Thread(target=self.animation_loop, daemon=True).start()
        self.input.start()
        
        root = tk.Tk(); root.title("Conveyor Runner")
        root.geometry("240x80"); root.attributes("-topmost", True)
        tk.Label(root, text="Conveyor is Active", font=("Segoe UI", 10, "bold"), fg="#0078d7").pack(pady=2)
        
        self.count_var = tk.StringVar(value="Detected: 0 windows")
        tk.Label(root, textvariable=self.count_var, font=("Segoe UI", 9)).pack()
        
        tk.Label(root, text="Alt + 1-4: Resize | Win+Alt + Scroll: Hyperscroll", font=("Segoe UI", 8), fg="#666666").pack(pady=1)
        root.protocol("WM_DELETE_WINDOW", lambda: self.hide_to_tray(root))
        
        def update_ui_info():
            if self.running:
                count = len(self.wm.managed_hwnds)
                self.count_var.set(f"Detected: {count} windows")
                root.after(1000, update_ui_info)
        
        update_ui_info()
        
        root.after(3000, lambda: self.hide_to_tray(root))
        
        # Start Tray in background
        threading.Thread(target=self.setup_tray, args=(root,), daemon=True).start()
        
        root.mainloop()

    def hide_to_tray(self, root):
        root.withdraw()

    def setup_tray(self, root):
        from PIL import Image, ImageDraw
        import pystray
        
        def create_image():
            width = 64; height = 64
            image = Image.new('RGB', (width, height), (30, 30, 30))
            dc = ImageDraw.Draw(image)
            dc.ellipse([10, 10, 54, 54], fill=(0, 120, 215))
            return image

        def on_tray_click(icon, item):
            if str(item) == "Show":
                root.after(0, root.deiconify)
            elif str(item) == "Exit":
                icon.stop()
                os._exit(0)

        menu = pystray.Menu(
            pystray.MenuItem("Show", on_tray_click),
            pystray.MenuItem("Exit", on_tray_click)
        )
        icon = pystray.Icon("Conveyor", create_image(), "Project Conveyor", menu)
        icon.run()

if __name__ == "__main__":
    app = HyperscrollApp()
    app.start()
