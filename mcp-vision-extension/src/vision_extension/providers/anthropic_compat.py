"""Anthropic Messages API (and Anthropic-compatible endpoints).

Used by: Anthropic native, Volcano Ark (/api/coding), AWS Bedrock proxies,
Vertex AI Anthropic endpoints, and any gateway speaking the Messages format.

The image content shape is different from OpenAI:
{"type": "image", "source": {"type": "base64", "media_type": "...", "data": "..."}}
"""

from __future__ import annotations

import httpx

from vision_extension.image_utils import to_base64
from vision_extension.providers.base import ImagePart, VisionProvider


class AnthropicProvider(VisionProvider):
    def describe(self, images: list[ImagePart], prompt: str) -> str:
        content: list[dict] = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": img.mime,
                    "data": to_base64(img.data),
                },
            }
            for img in images
        ]
        content.append({"type": "text", "text": prompt})

        body = {
            "model": self.cfg.model,
            "max_tokens": self.cfg.max_tokens,
            "temperature": self.cfg.temperature,
            "messages": [{"role": "user", "content": content}],
        }
        headers = {
            "x-api-key": self.cfg.api_key,
            "Authorization": f"Bearer {self.cfg.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "vision-extension/0.1",
            **self.cfg.extra_headers,
        }
        url = f"{self.cfg.base_url}/messages"

        with httpx.Client(timeout=self.cfg.timeout) as client:
            r = client.post(url, json=body, headers=headers)

        if r.status_code >= 400:
            raise RuntimeError(f"Vision API error {r.status_code}: {r.text[:600]}")

        data = r.json()
        try:
            blocks = data["content"]
        except KeyError as exc:
            raise RuntimeError(f"Unexpected response shape: {data!r}") from exc

        parts = []
        for b in blocks:
            if isinstance(b, dict) and b.get("type") == "text":
                parts.append(b.get("text", ""))
        return "".join(parts)
