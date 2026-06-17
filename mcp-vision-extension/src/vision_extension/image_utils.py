"""Image loading, resizing, and base64 encoding.

Pillow is optional. If installed, oversize images are downscaled in-memory
to keep API costs down. If not, images are sent as-is and a stderr warning
fires for files over ~2 MB.
"""

from __future__ import annotations

import base64
import hashlib
import io
import mimetypes
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import httpx

try:  # optional dep
    from PIL import Image  # type: ignore[import-not-found]

    HAS_PIL = True
except ImportError:
    HAS_PIL = False


SUPPORTED_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
LARGE_IMAGE_BYTES = 2 * 1024 * 1024


def _normalize_path(path: str) -> Path:
    p = Path(path).expanduser()
    if not p.is_absolute() and os.sep == "\\":
        p = Path(str(p).replace("/", "\\"))
    return p


def _is_url(s: str) -> bool:
    try:
        u = urlparse(s)
        return u.scheme in ("http", "https")
    except Exception:
        return False


def _fetch_url(url: str, timeout: float = 30.0) -> tuple[bytes, str]:
    with httpx.Client(timeout=timeout, follow_redirects=True) as c:
        r = c.get(url)
        r.raise_for_status()
        ct = r.headers.get("content-type", "image/png").split(";")[0].strip()
        if not ct.startswith("image/"):
            ct = "image/png"
        return r.content, ct


def _read_local(path_str: str) -> tuple[bytes, str]:
    p = _normalize_path(path_str)
    if not p.is_file():
        raise FileNotFoundError(f"Image not found: {path_str}")
    if p.suffix.lower() not in SUPPORTED_EXT:
        raise ValueError(
            f"Unsupported image extension {p.suffix!r}. Supported: {sorted(SUPPORTED_EXT)}"
        )
    mime, _ = mimetypes.guess_type(str(p))
    if not mime or not mime.startswith("image/"):
        mime = "image/png"
    return p.read_bytes(), mime


def _maybe_resize(data: bytes, mime: str, max_dim: int) -> tuple[bytes, str]:
    if not HAS_PIL or max_dim <= 0:
        if len(data) > LARGE_IMAGE_BYTES and not HAS_PIL:
            print(
                f"[vision-extension] warn: image is {len(data) // 1024} KB; install Pillow to auto-resize",
                file=sys.stderr,
            )
        return data, mime
    try:
        img = Image.open(io.BytesIO(data))
        w, h = img.size
        if max(w, h) <= max_dim:
            return data, mime
        scale = max_dim / max(w, h)
        new_size = (int(w * scale), int(h * scale))
        resized = img.resize(new_size, Image.LANCZOS)
        buf = io.BytesIO()
        fmt = "PNG" if mime == "image/png" else "JPEG"
        if fmt == "JPEG" and resized.mode in ("RGBA", "P"):
            resized = resized.convert("RGB")
        resized.save(buf, format=fmt, quality=88 if fmt == "JPEG" else None)
        return buf.getvalue(), f"image/{fmt.lower()}"
    except Exception as exc:
        print(f"[vision-extension] warn: resize failed ({exc}); sending original", file=sys.stderr)
        return data, mime


def load_image(path_or_url: str, max_dim: int) -> tuple[bytes, str, str]:
    """Return (raw_bytes, mime_type, sha256_hex) for caching.

    sha256 is computed AFTER resize so cache keys match the actual API payload.
    """
    if _is_url(path_or_url):
        data, mime = _fetch_url(path_or_url)
    else:
        data, mime = _read_local(path_or_url)
    data, mime = _maybe_resize(data, mime, max_dim)
    digest = hashlib.sha256(data).hexdigest()
    return data, mime, digest


def to_base64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def to_data_url(data: bytes, mime: str) -> str:
    return f"data:{mime};base64,{to_base64(data)}"
