import json
from pathlib import Path
import zoneinfo


SETTINGS_PATH = Path("settings.json")

def load_settings():
    if not SETTINGS_PATH.exists():
        raise FileNotFoundError(f"Settings file not found: {SETTINGS_PATH}")
    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_settings(data: dict):
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def get_db_path():
    settings = load_settings()
    return settings["database"]["url"]

def get_timezone():
    settings = load_settings()
    return zoneinfo.ZoneInfo(settings["app"]["default_timezone"])
