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
