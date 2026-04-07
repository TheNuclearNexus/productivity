import json
import os
from dataclasses import dataclass, asdict

@dataclass
class AppConfig:
    provider: str = "ollama"
    ollama_model: str = "llama3.1:8b"
    gemini_api_key: str = ""

class ConfigManager:
    """Manages global application configurations natively."""
    
    def __init__(self, filepath="config.json"):
        self.filepath = filepath
        self.config = AppConfig()
        self.load()

    def load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    data = json.load(f)
                    self.config = AppConfig(**data)
            except Exception as e:
                print(f"Failed to load config: {e}")

    def save(self):
        try:
            with open(self.filepath, "w") as f:
                json.dump(asdict(self.config), f, indent=4)
        except Exception as e:
            print(f"Failed to save config: {e}")
