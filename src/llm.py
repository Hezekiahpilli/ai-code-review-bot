import os
from typing import Optional
import httpx

OPENAI_BASE = os.getenv("OPENAI_BASE", "https://api.openai.com/v1")
ANTHROPIC_BASE = os.getenv("ANTHROPIC_BASE", "https://api.anthropic.com")

class LLMClient:
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")

    def available_provider(self) -> str:
        if self.openai_key:
            return "openai"
        if self.anthropic_key:
            return "anthropic"
        raise RuntimeError("No LLM provider configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY.")

    async def complete(self, system: str, user: str) -> str:
        provider = self.available_provider()
        if provider == "openai":
            return await self._openai(system, user)
        else:
            return await self._anthropic(system, user)

    async def _openai(self, system: str, user: str) -> str:
        headers = {"Authorization": f"Bearer {self.openai_key}"}
        payload = {"model": self.openai_model, "messages": [{"role":"system","content":system},{"role":"user","content":user}], "temperature": 0.2}
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(f"{OPENAI_BASE}/chat/completions", json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"]

    async def _anthropic(self, system: str, user: str) -> str:
        headers = {"x-api-key": self.anthropic_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
        payload = {"model": self.anthropic_model, "max_tokens": 2000, "system": system, "messages": [{"role":"user", "content": user}], "temperature": 0.2}
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(f"{ANTHROPIC_BASE}/v1/messages", json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
            blocks = data.get("content", [])
            text = "".join([b.get("text","") for b in blocks if b.get("type")=="text"])
            return text or "No content returned from provider"
