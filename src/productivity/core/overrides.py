import json
import os
from typing import Dict

class OverridesManager:
    """Manages manually overridden relevancy scores mapped by Window Title."""
    def __init__(self, filepath: str = "overrides.json"):
        self.filepath = filepath
        # Structure: {"Profile Name": {"Window Title": 1.0}}
        self.overrides: Dict[str, Dict[str, float]] = {}
        self.load()

    def load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    self.overrides = json.load(f)
            except Exception as e:
                print(f"Failed to load overrides: {e}")
                self.overrides = {}
        else:
            self.overrides = {}

    def save(self):
        try:
            with open(self.filepath, "w") as f:
                json.dump(self.overrides, f, indent=4)
        except Exception as e:
            print(f"Failed to save overrides: {e}")

    def get_override(self, profile_name: str, window_title: str):
        if profile_name in self.overrides:
            if window_title in self.overrides[profile_name]:
                entry = self.overrides[profile_name][window_title]
                if isinstance(entry, dict):
                    return entry
                return {"score": float(entry), "pretty_name": window_title}
        return None

    def get_score(self, profile_name: str, window_title: str):
        if profile_name in self.overrides:
            if window_title in self.overrides[profile_name]:
                entry = self.overrides[profile_name][window_title]
                if isinstance(entry, dict):
                    return float(entry.get("score", 0.5))
                return float(entry)
        return None

    def set_score(self, profile_name: str, window_title: str, score: float, pretty_name: str = None):
        if profile_name not in self.overrides:
            self.overrides[profile_name] = {}
            
        pretty_name = pretty_name or window_title
        self.overrides[profile_name][window_title] = {
            "score": float(score),
            "pretty_name": pretty_name
        }
        self.save()
