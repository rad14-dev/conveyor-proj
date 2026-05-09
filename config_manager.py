import json
import os
from pynput import keyboard

import sys

class ConfigManager:
    def __init__(self):
        # Determine path for config: prefer local directory for user edits
        self.config_path = "conveyor_config.json"
        
        # If config doesn't exist locally, check if we have a bundled one (PyInstaller)
        if not os.path.exists(self.config_path):
            if hasattr(sys, '_MEIPASS'):
                bundled_path = os.path.join(sys._MEIPASS, "conveyor_config.json")
                if os.path.exists(bundled_path):
                    self.config_path = bundled_path

        self.default_config = {
            "modifier": "alt_l",
            "window_gap": 5,
            "shortcuts": {
                "swap_left": "n",
                "swap_right": "m",
                "resize_1": "1",
                "resize_2": "2",
                "resize_3": "3",
                "resize_4": "4",
                "toggle_floating": "v",
                "nav_left": "left",
                "nav_right": "right"
            }
        }
        self.config = self.load_config()
        self.modifier_keys = self.get_modifier_keys()

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    return json.load(f)
            except:
                return self.default_config
        return self.default_config

    def save_config(self, shortcuts=None, gap=None):
        if shortcuts:
            self.config["shortcuts"] = shortcuts
        if gap is not None:
            self.config["window_gap"] = gap
            
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=4)
        
        self.modifier_keys = self.get_modifier_keys()

    def get_modifier_keys(self):
        # Support both singular and plural keys for compatibility
        mod_list = self.config.get("modifiers") or self.config.get("modifier") or ["alt_l"]
        if isinstance(mod_list, str): mod_list = [mod_list]
        
        keys = []
        for mod_str in mod_list:
            mod_str = mod_str.lower()
            if "alt_l" in mod_str: keys.append(keyboard.Key.alt_l)
            elif "alt_r" in mod_str: keys.append(keyboard.Key.alt_r)
            elif "win" in mod_str or "cmd" in mod_str: keys.append(keyboard.Key.cmd_l)
            elif "ctrl" in mod_str: keys.append(keyboard.Key.ctrl_l)
            elif "shift" in mod_str: keys.append(keyboard.Key.shift)
        return keys if keys else [keyboard.Key.alt_l]

    @property
    def shortcuts(self):
        return self.config.get("shortcuts", self.default_config["shortcuts"])
