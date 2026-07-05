import json
import os
import dataclasses
from models.settings import AppSettings

CONFIG_FILE = "config.json"

class ConfigManager:
    @staticmethod
    def load() -> AppSettings:
        if not os.path.exists(CONFIG_FILE):
            return AppSettings()
        
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                # Filter out keys not in AppSettings to avoid errors on updates
                valid_keys = {f.name for f in dataclasses.fields(AppSettings)}
                filtered_data = {k: v for k, v in data.items() if k in valid_keys}
                return AppSettings(**filtered_data)
        except Exception:
            return AppSettings()
            
    @staticmethod
    def save(settings: AppSettings):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(dataclasses.asdict(settings), f, indent=4)
        except Exception as e:
            print(f"Failed to save config: {e}")
