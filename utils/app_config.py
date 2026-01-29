import json
import os
import platform
from pathlib import Path
from typing import Any


class AppConfig:
    def __init__(self):
        self.app_name = "I2 Localization Manager"
        self.company_name = "veydzh3r"

        self.app_dir = self.get_app_directory()
        self.config_path = self.app_dir / "config.json"
        self.recent_path = self.app_dir / "recent.json"

        self.recent = {}
        self.config = {}

        try:
            self.load_config()
            self.load_recent_files()
        except PermissionError as e:
            raise PermissionError(f"[CONFIG] Permission Error: {str(e)}") from e
        except OSError as e:
            raise OSError(f"[CONFIG] Input/Output Error: {str(e)}") from e

    def get_app_directory(self):
        if platform.system() == "Windows":
            base_dir = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
        else:
            base_dir = Path.home() / ".config"

        app_dir = base_dir / self.company_name / self.app_name
        app_dir.mkdir(parents=True, exist_ok=True)
        return app_dir

    def get_recent_files(self):
        return self.recent.get("files", [])

    def add_recent_file(self, file_path: str):
        if not os.path.isfile(file_path):
            return

        files = self.get_recent_files()
        if file_path in files:
            files.remove(file_path)
        files.insert(0, file_path)
        self.recent["files"] = files[:10]
        self.save_recent_files()

    def remove_recent_file(self, file_path: str):
        self.get_recent_files().remove(file_path)
        self.save_recent_files()

    def load_recent_files(self):
        if self.recent_path.exists():
            with open(self.recent_path, "r", encoding="utf-8") as f:
                self.recent = json.load(f)
        else:
            self.recent = {"files": []}
            self.save_recent_files()

    def clear_recent_files(self):
        if self.recent.get("files", []):
            self.recent = {"files": []}
            self.save_recent_files()

    def save_recent_files(self):
        with open(self.recent_path, "w", encoding="utf-8") as f:
            json.dump(self.recent, f, indent=2)

    def load_config(self):
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        else:
            print(f"[CONFIG] Could not find the configuration file, creating one with defaults...")
            self.config = {"check_updates_on_startup": False, "language": "en-US", "theme": "Fusion"}
            self.save_config()

    def save_config(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)

    def get_config(self, key: str, default: Any = None):
        return self.config.get(key, default)

    def set_config(self, key: str, value: Any):
        self.config[key] = value
        self.save_config()


config = AppConfig()
