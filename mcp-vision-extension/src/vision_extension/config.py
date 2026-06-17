"""Runtime configuration loaded from environment variables.

Single source of truth — no config files, no hidden defaults.
Every setting is one env var. Missing required vars fail fast at startup.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

Protocol = Literal["openai", "anthropic"]
Lang = Literal["auto", "en", "zh"]


@dataclass(frozen=True)
class Config:
    protocol: Protocol
    base_url: str
    api_key: str
    model: str
    max_tokens: int
    temperature: float
    lang: Lang
    max_image_dim: int
    cache_enabled: bool
    cache_dir: str
    timeout: float
    extra_headers: dict[str, str]

    @classmethod
    def from_env(cls) -> "Config":
        protocol = os.environ.get("VISION_EXTENSION_PROTOCOL", "openai").lower()
        if protocol not in ("openai", "anthropic"):
            raise RuntimeError(
                f"VISION_EXTENSION_PROTOCOL must be 'openai' or 'anthropic', got {protocol!r}"
            )

        base_url = os.environ.get("VISION_EXTENSION_BASE_URL", "").rstrip("/")
        api_key = os.environ.get("VISION_EXTENSION_API_KEY", "")
        model = os.environ.get("VISION_EXTENSION_MODEL", "")

        if not base_url:
            raise RuntimeError("VISION_EXTENSION_BASE_URL is required")
        if not api_key:
            raise RuntimeError("VISION_EXTENSION_API_KEY is required")
        if not model:
            raise RuntimeError("VISION_EXTENSION_MODEL is required")

        lang = os.environ.get("VISION_EXTENSION_LANG", "auto").lower()
        if lang not in ("auto", "en", "zh"):
            raise RuntimeError(f"VISION_EXTENSION_LANG must be auto/en/zh, got {lang!r}")

        extra_headers: dict[str, str] = {}
        if protocol == "anthropic":
            version = os.environ.get("VISION_EXTENSION_ANTHROPIC_VERSION", "2023-06-01")
            extra_headers["anthropic-version"] = version

        return cls(
            protocol=protocol,  # type: ignore[arg-type]
            base_url=base_url,
            api_key=api_key,
            model=model,
            max_tokens=int(os.environ.get("VISION_EXTENSION_MAX_TOKENS", "1536")),
            temperature=float(os.environ.get("VISION_EXTENSION_TEMPERATURE", "0.2")),
            lang=lang,  # type: ignore[arg-type]
            max_image_dim=int(os.environ.get("VISION_EXTENSION_MAX_IMAGE_DIM", "2048")),
            cache_enabled=os.environ.get("VISION_EXTENSION_CACHE_ENABLED", "true").lower()
            in ("1", "true", "yes"),
            cache_dir=os.environ.get(
                "VISION_EXTENSION_CACHE_DIR",
                os.path.join(os.path.expanduser("~"), ".cache", "vision-extension"),
            ),
            timeout=float(os.environ.get("VISION_EXTENSION_TIMEOUT", "90")),
            extra_headers=extra_headers,
        )
