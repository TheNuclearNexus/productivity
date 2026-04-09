import re
from productivity.llm.client import OllamaClient
from productivity.core.profile import FocusProfile

from productivity.core.overrides import OverridesManager

from productivity.core.config import AppConfig


class WindowClassifier:
    def __init__(self, config: AppConfig, overrides_mgr: OverridesManager = None):
        self.config = config

        if config.provider == "gemini" and config.gemini_api_key.strip():
            from productivity.llm.client import GeminiClient

            self.client = GeminiClient(api_key=config.gemini_api_key.strip())
            self.model = "gemini-3.1-flash-lite-preview"
        else:
            from productivity.llm.client import OllamaClient

            self.client = OllamaClient()
            self.model = config.ollama_model

        self.overrides = overrides_mgr
        # Simple in-memory cache mapped robustly to a JSON file explicitly
        self._cache = {}
        self.load_cache()

    def load_cache(self):
        import os
        import json

        if os.path.exists("llm_cache.json"):
            try:
                with open("llm_cache.json", "r") as f:
                    data = json.load(f)
                for profile_name, apps in data.items():
                    for title, val in apps.items():
                        if isinstance(val, dict):
                            self._cache[(title, profile_name)] = val
                        else:
                            self._cache[(title, profile_name)] = {
                                "score": float(val),
                                "pretty_name": title,
                            }
            except Exception:
                pass

    def save_cache(self):
        import json

        data = {}
        for (title, profile_name), score in self._cache.items():
            if profile_name not in data:
                data[profile_name] = {}
            data[profile_name][title] = score
        try:
            with open("llm_cache.json", "w") as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass

    from typing import Tuple

    async def classify(
        self, window_title: str, profile: FocusProfile
    ) -> Tuple[float, str]:
        """
        Classify the window title based on the given focus profile.
        Returns a relevance score (0.0-1.0) and a clean, succinct 'pretty_name'.
        """
        if not window_title or window_title == "Unknown":
            return 0.5, window_title

        if self.overrides:
            override_entry = self.overrides.get_override(profile.name, window_title)
            if override_entry is not None:
                self._cache[(window_title, profile.name)] = override_entry
                return override_entry.get("score", 0.5), override_entry.get(
                    "pretty_name", window_title
                )

        cache_key = (window_title, profile.name)
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            return entry.get("score", 0.5), entry.get("pretty_name", window_title)

        prompt = (
            f"You are an AI productivity assistant. The user is focusing on '{profile.name}'. "
            f"Context: {profile.description}\n\n"
            f"Rate the relevance of the following window on a scale of 0.0 (distraction) to 1.0 (highly relevant).\n"
            f"Also, extract the application's title or in the case of browser tabs, the website name, 'pretty_name' for this window (e.g. extracting main titles from long browser tabs, removing verbose application suffixes, dropping URLs). Max 3-8 words natively.\n\n"
            "If the window title alone is an accurate name, then just return that. Do not add any additional information."
            f'Window Title: "{window_title}"\n\n'
            f"Respond EXCLUSIVELY in this exact JSON format:\n"
            f"{{\n"
            f'  "score": 0.8,\n'
            f'  "pretty_name": "Google Docs"\n'
            f"}}"
        )

        response = await self.client.generate(
            prompt=prompt, model=self.model, json_mode=True
        )

        score = 0.5
        pretty_name = window_title

        if response:
            import json

            try:
                data = json.loads(response)
                score = float(data.get("score", 0.5))
                score = max(0.0, min(1.0, score))
                pretty_name = str(data.get("pretty_name", window_title))
            except Exception:
                import re

                match = re.search(r"0\.\d+|1\.0|0|1", response)
                if match:
                    score = float(match.group())
                    score = max(0.0, min(1.0, score))

        self._cache[cache_key] = {"score": score, "pretty_name": pretty_name}
        self.save_cache()

        print(f"[{pretty_name}] scored: {score}, original: {window_title}")
        return score, pretty_name
