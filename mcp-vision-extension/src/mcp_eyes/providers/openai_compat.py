"""OpenAI-compatible Chat Completions API.

Used by: OpenAI, Volcano Ark (/api/coding/v3), DeepSeek, Qwen / DashScope,
SiliconFlow, OpenRouter, Together, Groq, Ollama, Zhipu (GLM-4V), and most
local servers exposing /v1/chat/completions.
"""

from __future__ import annotations

import httpx

from mcp_eyes.image_utils import to_data_url
from mcp_eyes.providers.base import ImagePart, VisionProvider


class OpenAIProvider(VisionProvider):
    def describe(self, images: list[ImagePart], prompt: str) -> str:
        content: list[dict] = [
            {"type": "image_url", "image_url": {"url": to_data_url(img.data, img.mime)}}
            for img in images
        ]
        content.append({"type": "text", "text": prompt})

        body = {
            "model": self.cfg.model,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": self.cfg.max_tokens,
            "temperature": self.cfg.temperature,
        }
        headers = {
            "Authorization": f"Bearer {self.cfg.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "mcp-eyes/0.1",
            **self.cfg.extra_headers,
        }
        url = f"{self.cfg.base_url}/chat/completions"

        with httpx.Client(timeout=self.cfg.timeout) as client:
            r = client.post(url, json=body, headers=headers)

        if r.status_code >= 400:
            raise RuntimeError(f"Vision API error {r.status_code}: {r.text[:600]}")

        data = r.json()
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise RuntimeError(f"Unexpected response shape: {data!r}") from exc
        if isinstance(text, list):
            text = "".join(p.get("text", "") for p in text if isinstance(p, dict))
        return text or ""
