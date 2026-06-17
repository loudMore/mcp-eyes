"""MCP server (JSON-RPC over stdio).

Exposes three tools: describe_image, compare_images, extract_text.
The reasoning model that calls these tools never sees the raw bytes —
only the structured text the vision model produces under the eyes-only protocol.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any

from mcp_eyes import __version__
from mcp_eyes.config import Config
from mcp_eyes.image_utils import load_image
from mcp_eyes.prompts import SCENES, build_prompt, detect_lang
from mcp_eyes.providers import make_provider
from mcp_eyes.providers.base import ImagePart


def _log(msg: str) -> None:
    sys.stderr.write(f"[mcp-eyes] {msg}\n")
    sys.stderr.flush()


def _send(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _ok(req_id: Any, result: Any) -> None:
    _send({"jsonrpc": "2.0", "id": req_id, "result": result})


def _err(req_id: Any, code: int, message: str) -> None:
    _send({"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}})


# ------------- caching -------------

def _cache_key(image_hashes: list[str], prompt: str, model: str) -> str:
    h = hashlib.sha256()
    for ih in image_hashes:
        h.update(ih.encode())
        h.update(b"|")
    h.update(model.encode())
    h.update(b"|")
    h.update(prompt.encode("utf-8"))
    return h.hexdigest()


def _cache_get(cfg: Config, key: str) -> str | None:
    if not cfg.cache_enabled:
        return None
    p = Path(cfg.cache_dir) / f"{key}.txt"
    if p.is_file():
        try:
            return p.read_text(encoding="utf-8")
        except OSError:
            return None
    return None


def _cache_put(cfg: Config, key: str, value: str) -> None:
    if not cfg.cache_enabled:
        return
    try:
        d = Path(cfg.cache_dir)
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{key}.txt").write_text(value, encoding="utf-8")
    except OSError as exc:
        _log(f"cache write failed: {exc}")


# ------------- tool definitions -------------

SCENE_ENUM = list(SCENES)

TOOLS = [
    {
        "name": "describe_image",
        "description": (
            "Describe a local image or URL using a vision model that's locked to "
            "EYES-ONLY mode (no advice, no reasoning, no opinions — pure objective "
            "description). Use this whenever the user references an image, screenshot, "
            "diagram, error dialog, UI mockup, code screenshot, or game frame. "
            "Returns structured text the calling reasoning model can analyze."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "image": {
                    "type": "string",
                    "description": "Local file path (absolute) or http(s) URL. PNG/JPG/WEBP/GIF/BMP.",
                },
                "question": {
                    "type": "string",
                    "description": "Specific question to focus the description (optional). Examples: 'What does the red-circled element show?', 'Transcribe the error stack verbatim'.",
                },
                "scene": {
                    "type": "string",
                    "enum": SCENE_ENUM,
                    "description": "Scene preset for prompt template. 'auto' picks via keyword detection. Choose explicitly when the question is ambiguous.",
                    "default": "auto",
                },
                "bypass_cache": {
                    "type": "boolean",
                    "description": "Force re-call even if a cached result exists.",
                    "default": False,
                },
            },
            "required": ["image"],
        },
    },
    {
        "name": "compare_images",
        "description": (
            "Send multiple images to the vision model in a single call to compare them. "
            "Use for before/after, diff screenshots, or any multi-image question. The "
            "vision model still operates in eyes-only mode."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "images": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 2,
                    "maxItems": 6,
                    "description": "Local paths or URLs, in the order they should be compared.",
                },
                "question": {
                    "type": "string",
                    "description": "What to compare (optional).",
                },
                "scene": {
                    "type": "string",
                    "enum": SCENE_ENUM,
                    "default": "comparison",
                },
                "bypass_cache": {"type": "boolean", "default": False},
            },
            "required": ["images"],
        },
    },
    {
        "name": "extract_text",
        "description": (
            "Pure OCR shortcut. Returns the verbatim text from an image with no "
            "interpretation. Equivalent to describe_image with scene='ocr'."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "image": {"type": "string", "description": "Local path or URL."},
                "bypass_cache": {"type": "boolean", "default": False},
            },
            "required": ["image"],
        },
    },
]


# ------------- core dispatch -------------

def _run_describe(
    cfg: Config,
    images_arg: list[str],
    question: str,
    scene: str,
    bypass_cache: bool,
) -> str:
    parts: list[ImagePart] = []
    hashes: list[str] = []
    for src in images_arg:
        data, mime, digest = load_image(src, cfg.max_image_dim)
        parts.append(ImagePart(data=data, mime=mime))
        hashes.append(digest)

    lang = detect_lang(question, cfg.lang)
    prompt = build_prompt(scene, question, lang)
    key = _cache_key(hashes, prompt, cfg.model)

    if not bypass_cache:
        cached = _cache_get(cfg, key)
        if cached is not None:
            _log(f"cache hit ({key[:12]})")
            return cached

    provider = make_provider(cfg)
    text = provider.describe(parts, prompt)
    _cache_put(cfg, key, text)
    return text


def _handle_tool_call(cfg: Config, name: str, args: dict, req_id: Any) -> None:
    try:
        if name == "describe_image":
            image = args.get("image") or args.get("image_path") or args.get("url")
            if not image:
                _err(req_id, -32602, "missing parameter 'image'")
                return
            text = _run_describe(
                cfg,
                [image],
                args.get("question") or "",
                args.get("scene") or "auto",
                bool(args.get("bypass_cache")),
            )

        elif name == "compare_images":
            images = args.get("images") or []
            if not isinstance(images, list) or len(images) < 2:
                _err(req_id, -32602, "'images' must be a list of >=2 paths/URLs")
                return
            text = _run_describe(
                cfg,
                images,
                args.get("question") or "",
                args.get("scene") or "comparison",
                bool(args.get("bypass_cache")),
            )

        elif name == "extract_text":
            image = args.get("image") or args.get("image_path") or args.get("url")
            if not image:
                _err(req_id, -32602, "missing parameter 'image'")
                return
            text = _run_describe(
                cfg, [image], "", "ocr", bool(args.get("bypass_cache"))
            )

        else:
            _err(req_id, -32601, f"unknown tool: {name}")
            return

        _ok(
            req_id,
            {"content": [{"type": "text", "text": text}], "isError": False},
        )
    except Exception as exc:
        _log(f"tool {name} failed: {exc}\n{traceback.format_exc()}")
        _ok(
            req_id,
            {
                "content": [{"type": "text", "text": f"vision call failed: {exc}"}],
                "isError": True,
            },
        )


def _handle_request(cfg: Config, req: dict) -> None:
    method = req.get("method")
    req_id = req.get("id")
    params = req.get("params") or {}

    if method == "initialize":
        _ok(
            req_id,
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "mcp-eyes", "version": __version__},
            },
        )
        return

    if method in ("notifications/initialized", "initialized"):
        return

    if method == "tools/list":
        _ok(req_id, {"tools": TOOLS})
        return

    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments") or {}
        _handle_tool_call(cfg, name, args, req_id)
        return

    if method == "ping":
        _ok(req_id, {})
        return

    if req_id is not None:
        _err(req_id, -32601, f"method not implemented: {method}")


def main() -> None:
    try:
        sys.stdin.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

    try:
        cfg = Config.from_env()
    except RuntimeError as exc:
        _log(f"config error: {exc}")
        sys.exit(2)

    _log(
        f"start v{__version__} protocol={cfg.protocol} model={cfg.model} "
        f"base={cfg.base_url} lang={cfg.lang} cache={cfg.cache_enabled}"
    )

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as exc:
            _log(f"bad json: {exc}")
            continue
        try:
            _handle_request(cfg, req)
        except Exception as exc:
            _log(f"handler crashed: {exc}\n{traceback.format_exc()}")


if __name__ == "__main__":
    main()
