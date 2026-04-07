import json
import os
import re
from dataclasses import dataclass, asdict


@dataclass
class FocusProfile:
    name: str
    description: str


class ProfileManager:
    """Manages parsing and persistence of custom LLM profiles natively."""

    def __init__(self, filepath="profiles.json"):
        self.filepath = filepath
        self.profiles = {}
        self.load()

    def generate_key(self, name: str) -> str:
        key = re.sub(r"[^a-z0-9]", "_", name.lower())
        return key.strip("_")

    def load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        self.profiles[k] = FocusProfile(**v)
            except Exception as e:
                print(f"Failed to load profiles: {e}")
                self._load_defaults()
        else:
            self._load_defaults()

    def _load_defaults(self):
        self.profiles = {
            "software_dev": FocusProfile(
                name="Software Development",
                description="Programming, coding, documentation, reading technical documentation, and using developer tools like IDEs or terminals.",
            ),
            "research": FocusProfile(
                name="Research",
                description="Reading articles, PDFs, academic papers, and using note-taking tools.",
            ),
            "general": FocusProfile(
                name="General Work",
                description="Answering emails, generic writing, messaging colleagues in Slack/Teams.",
            ),
        }
        self.save()

    def save(self):
        try:
            with open(self.filepath, "w") as f:
                data = {k: asdict(v) for k, v in self.profiles.items()}
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Failed to save profiles: {e}")
