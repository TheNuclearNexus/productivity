import httpx
from typing import Optional


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    async def generate(self, prompt: str, model: str = "llama3", json_mode: bool = False) -> Optional[str]:
        """Send a prompt to Ollama and get a text response."""
        url = f"{self.base_url}/api/generate"
        payload = {"model": model, "prompt": prompt, "stream": False}
        if json_mode:
            payload["format"] = "json"

        async with httpx.AsyncClient() as client:
            try:
                # 120 second timeout allows larger Ollama models time to load into VRAM
                response = await client.post(url, json=payload, timeout=120.0)
                response.raise_for_status()
                data = response.json()
                response = data.get("response", "").strip()
                return response
            except Exception as e:
                print(f"Ollama API Error: {e}")
                return None


class GeminiClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def generate(self, prompt: str, model: str = "gemini-3.1-flash-lite-preview", json_mode: bool = False) -> Optional[str]:
        """Send a prompt natively to Google's REST Endpoint implicitly requesting structured JSON."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        if json_mode:
            payload["generationConfig"] = {"responseMimeType": "application/json"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, timeout=30.0)
                response.raise_for_status()
                data = response.json()

                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
                return None
            except Exception as e:
                print(f"Gemini API Error: {e}")
                return None
