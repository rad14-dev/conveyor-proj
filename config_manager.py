import json
import os
from pynput import keyboard

class ConfigManager:
    def __init__(self):
        self.config_path = "conveyor_config.json"
        self.default_config = {
            "modifier": "alt_l",
            "window_gap": 5,
            "shortcuts": {
                "modifier": "alt_l",
                "swap_left": ",",
                "swap_right": ".",
                "resize_1": "1",
                "resize_2": "2",
                "resize_3": "3",
                "resize_4": "4",
                "nav_left": "left",
                "nav_right": "right"
            }
        }
        self.config = self.load_config()
        self.modifier_key = self.get_modifier_key()

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
            if "modifier" in shortcuts:
                self.config["modifier"] = shortcuts["modifier"]
        if gap is not None:
            self.config["window_gap"] = gap
            
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=4)
        
        self.modifier_key = self.get_modifier_key()

    def get_modifier_key(self):
        mod_str = self.config.get("modifier", "alt_l").lower()
        if mod_str == "alt_l": return keyboard.Key.alt_l
        if mod_str == "alt_r": return keyboard.Key.alt_r
        if mod_str == "ctrl_l": return keyboard.Key.ctrl_l
        if mod_str == "shift": return keyboard.Key.shift
        return keyboard.Key.alt_l

    @property
    def shortcuts(self):
        return self.config.get("shortcuts", self.default_config["shortcuts"])
