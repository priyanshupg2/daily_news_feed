import json
import logging

import httpx

logger = logging.getLogger(__name__)


class OllamaProvider:
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def complete(self, prompt: str, system: str = "") -> str:
        """Send a completion request to Ollama and return the response text."""
        payload: dict = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.base_url}/api/generate", json=payload
            )
            resp.raise_for_status()
            return resp.json()["response"]

    async def complete_json(
        self, prompt: str, system: str = "", schema: dict | None = None
    ) -> dict:
        """Send a completion request expecting JSON output."""
        payload: dict = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }
        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.base_url}/api/generate", json=payload
            )
            resp.raise_for_status()
            text = resp.json()["response"]
        # Same contract as ClaudeProvider: malformed JSON → empty dict
        # rather than an exception. Lets callers branch on `not result`
        # uniformly across providers.
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Ollama returned non-JSON text: %s", text[:200])
            stripped = (
                text.strip().removeprefix("```json").removeprefix("```")
                .removesuffix("```").strip()
            )
            try:
                return json.loads(stripped)
            except json.JSONDecodeError:
                return {}
