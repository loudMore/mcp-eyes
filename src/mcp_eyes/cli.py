"""Consolidated CLI for mcp-eyes.

Subcommands:
- init      : print/write a CLAUDE.md / AGENTS.md snippet for the project
- presets   : list known provider presets (machine-readable JSON or human table)
- config    : generate a .mcp.json from a preset + API key + optional overrides
- doctor    : self-check — env vars, server boot, optional API ping
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from mcp_eyes import __version__
from mcp_eyes.presets import (
    PRESETS,
    Preset,
    all_presets_dict,
    find_preset,
    preset_names,
)


# --------------------------- init ---------------------------

TEMPLATE_ZH = """## 视觉识图 (mcp-eyes)

**主模型{reasoning_clause}是纯文本推理模型，无法直接识别图片。**

本项目通过 MCP server `eyes`（[mcp-eyes](https://github.com/loudMore/mcp-eyes)）把视觉能力外挂给主模型。当前后端配置：

- 协议：`{protocol}`
- 视觉模型：`{vision_model}`
- API base：`{base_url}`

具体值在 `.mcp.json` 的环境变量里，切换其他视觉模型只改那里、不动这份文档。

### 三个工具

- `mcp__eyes__describe_image(image, question?, scene?)` — 单图结构化描述
- `mcp__eyes__compare_images(images[], question?)` — 多图对比
- `mcp__eyes__extract_text(image)` — 纯 OCR

### 必须知道的几条

1. **遇到任何图片路径或图片 URL（.png/.jpg/.jpeg/.webp/.gif/.bmp），必须调用 mcp-eyes**，不要用 Read 工具读图（图片字节流给纯文本模型必出错）。
2. **路径用绝对路径，正斜杠也吃**（`C:/Users/.../foo.png`）。
3. **视觉模型已在服务端被锁成 "eyes-only"**：不会给修复建议、不会推测原因、不会反问 —— 只做客观描述和逐字转录。推理、诊断、修复方案都由主模型来做，不要让视觉模型回答 "为什么 / 怎么修 / 哪里有问题"。
4. **`scene` 参数怎么选**：默认 `auto` 按问题关键词识别。手动可选 `general / annotated / ui / mockup / error / code / game / webpage / chat / terminal / diagram / comparison / table / lowquality / ocr`。
5. **`question` 怎么写**：问"看到什么"，别问"该怎么办"。
   - 好：「逐字转录报错堆栈，含文件路径和行号」
   - 好：「图中红圈圈出的是什么？」
   - 差：「为什么会报这个错？」（视觉模型不会回答）
6. **结果是数据不是答案**：拿到描述后由主模型分析综合，再回答用户。

### 缓存

同一张图 + 同一个 `question` + 同一个 `scene` + 同一个模型 = 命中本地缓存，零成本。要强制重调用传 `bypass_cache: true`。
"""

TEMPLATE_EN = """## Vision via mcp-eyes

**The reasoning model{reasoning_clause} is text-only and cannot see images.**

This project exposes vision capability through the `eyes` MCP server ([mcp-eyes](https://github.com/loudMore/mcp-eyes)). Current backend:

- Protocol: `{protocol}`
- Vision model: `{vision_model}`
- API base: `{base_url}`

Concrete values live in `.mcp.json` env vars. Swapping the vision model is config-only; this doc stays the same.

### Tools

- `mcp__eyes__describe_image(image, question?, scene?)` — single-image structured description
- `mcp__eyes__compare_images(images[], question?)` — multi-image comparison
- `mcp__eyes__extract_text(image)` — pure OCR

### Rules

1. **Whenever a local image path or http(s) image URL appears (.png/.jpg/.jpeg/.webp/.gif/.bmp), call mcp-eyes.** Never use Read on image bytes — that breaks the text model.
2. **Use absolute paths; forward slashes are fine** (`C:/Users/.../foo.png` on Windows).
3. **The vision model is locked into eyes-only mode** server-side: no advice, no opinions, no speculation, no follow-up questions — just verbatim transcription and structured description. Reasoning, diagnosis, and fix suggestions are the reasoning model's job. Never ask the vision model "why" or "how to fix".
4. **Picking `scene`**: default `auto` keyword-detects. Override with one of `general / annotated / ui / mockup / error / code / game / webpage / chat / terminal / diagram / comparison / table / lowquality / ocr`.
5. **Writing `question`**: ask what's visible, not what to do.
   - Good: "Transcribe the stack trace verbatim, including file paths and line numbers."
   - Good: "What does the red-circled element show?"
   - Bad: "Why is this failing?" — the vision model will refuse this part.
6. **The output is data, not the final answer**: synthesize and respond to the user from the description, don't forward it raw.

### Caching

Same image + same `question` + same `scene` + same model = local cache hit, zero cost. Pass `bypass_cache: true` to force a fresh call.
"""


def _safe_print(text: str) -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    try:
        sys.stdout.write(text)
        sys.stdout.flush()
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode("utf-8"))
        sys.stdout.buffer.flush()


def cmd_init(args: argparse.Namespace) -> int:
    template = TEMPLATE_ZH if args.lang == "zh" else TEMPLATE_EN
    if args.reasoning_model:
        if args.lang == "zh":
            reasoning_clause = f" `{args.reasoning_model}` "
        else:
            reasoning_clause = f" `{args.reasoning_model}`"
    else:
        reasoning_clause = ""
    snippet = template.format(
        reasoning_clause=reasoning_clause,
        protocol=os.environ.get("MCP_EYES_PROTOCOL", "<not-set>"),
        vision_model=os.environ.get("MCP_EYES_MODEL", "<not-set>"),
        base_url=os.environ.get("MCP_EYES_BASE_URL", "<not-set>"),
    )
    if args.out == "-":
        _safe_print(snippet)
    else:
        Path(args.out).write_text(snippet, encoding="utf-8")
        print(f"wrote {args.out}", file=sys.stderr)
    return 0


# --------------------------- presets ---------------------------

def cmd_presets(args: argparse.Namespace) -> int:
    if args.format == "json":
        sys.stdout.write(json.dumps(all_presets_dict(), ensure_ascii=False, indent=2))
        sys.stdout.write("\n")
        return 0

    rows = ["NAME              PROTOCOL    DEFAULT MODEL                    BASE URL"]
    rows.append("-" * 110)
    for p in PRESETS:
        rows.append(f"{p.name:18s}{p.protocol:12s}{p.default_model:34s}{p.base_url}")
        if p.aliases:
            rows.append(f"  aliases: {', '.join(p.aliases)}")
        rows.append(f"  notes: {p.notes}")
        rows.append("")
    print("\n".join(rows))
    return 0


# --------------------------- config ---------------------------

def _build_config_from_preset(preset: Preset, api_key: str, model_override: str | None) -> dict:
    return {
        "MCP_EYES_PROTOCOL": preset.protocol,
        "MCP_EYES_BASE_URL": preset.base_url,
        "MCP_EYES_API_KEY": api_key,
        "MCP_EYES_MODEL": model_override or preset.default_model,
        "MCP_EYES_LANG": "auto",
        "MCP_EYES_MAX_IMAGE_DIM": "2048",
        "MCP_EYES_CACHE_ENABLED": "true",
    }


def _build_config_from_flags(args: argparse.Namespace) -> dict:
    if not args.base_url:
        raise SystemExit("error: --base-url is required when --preset is not given")
    if not args.model:
        raise SystemExit("error: --model is required when --preset is not given")
    return {
        "MCP_EYES_PROTOCOL": args.protocol,
        "MCP_EYES_BASE_URL": args.base_url,
        "MCP_EYES_API_KEY": args.api_key,
        "MCP_EYES_MODEL": args.model,
        "MCP_EYES_LANG": "auto",
        "MCP_EYES_MAX_IMAGE_DIM": "2048",
        "MCP_EYES_CACHE_ENABLED": "true",
    }


def cmd_config(args: argparse.Namespace) -> int:
    if not args.api_key:
        raise SystemExit("error: --api-key is required")

    if args.preset:
        preset = find_preset(args.preset)
        if not preset:
            raise SystemExit(
                f"error: unknown preset {args.preset!r}. Run 'mcp-eyes presets' for the full list."
            )
        env = _build_config_from_preset(preset, args.api_key, args.model)
    else:
        env = _build_config_from_flags(args)

    server_block = {
        "command": args.python or sys.executable,
        "args": ["-m", "mcp_eyes"],
        "env": env,
    }

    if args.server_name:
        full = {"mcpServers": {args.server_name: server_block}}
    else:
        full = {"mcpServers": {"eyes": server_block}}

    out_text = json.dumps(full, indent=2, ensure_ascii=False)

    if args.out == "-":
        _safe_print(out_text + "\n")
    else:
        if args.merge and Path(args.out).is_file():
            existing = json.loads(Path(args.out).read_text(encoding="utf-8"))
            existing.setdefault("mcpServers", {})
            existing["mcpServers"].update(full["mcpServers"])
            Path(args.out).write_text(
                json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            print(f"merged into {args.out}", file=sys.stderr)
        else:
            Path(args.out).write_text(out_text, encoding="utf-8")
            print(f"wrote {args.out}", file=sys.stderr)
    return 0


# --------------------------- doctor ---------------------------

def cmd_doctor(args: argparse.Namespace) -> int:
    print(f"mcp-eyes {__version__} doctor")
    print("=" * 50)
    ok = True

    # 1. env vars
    print("\n[1/4] environment variables")
    required = ("MCP_EYES_PROTOCOL", "MCP_EYES_BASE_URL", "MCP_EYES_API_KEY", "MCP_EYES_MODEL")
    for k in required:
        v = os.environ.get(k, "")
        if not v:
            print(f"  MISSING  {k}")
            ok = False
        else:
            shown = v if k != "MCP_EYES_API_KEY" else (v[:8] + "..." + v[-4:] if len(v) > 12 else "***")
            print(f"  ok       {k}={shown}")

    # 2. dependencies
    print("\n[2/4] python dependencies")
    try:
        import httpx  # noqa: F401
        print("  ok       httpx installed")
    except ImportError:
        print("  MISSING  httpx — run: pip install httpx")
        ok = False
    try:
        from PIL import Image  # noqa: F401
        print("  ok       Pillow installed (image auto-resize enabled)")
    except ImportError:
        print("  warn     Pillow not installed (image auto-resize off; large images send raw)")

    # 3. server boot
    print("\n[3/4] server boots")
    if not ok:
        print("  skip     fix env vars first")
    else:
        try:
            from mcp_eyes.config import Config

            cfg = Config.from_env()
            print(f"  ok       protocol={cfg.protocol} model={cfg.model}")
        except Exception as exc:
            print(f"  fail     {exc}")
            ok = False

    # 4. live API ping (optional)
    print("\n[4/4] live API ping")
    if args.skip_api:
        print("  skip     --skip-api")
    elif not ok:
        print("  skip     prior step failed")
    else:
        if not args.image:
            print("  skip     no --image given (pass a small test image to verify the API works)")
        else:
            try:
                from mcp_eyes.config import Config
                from mcp_eyes.image_utils import load_image
                from mcp_eyes.prompts import build_prompt
                from mcp_eyes.providers import make_provider
                from mcp_eyes.providers.base import ImagePart

                cfg = Config.from_env()
                t0 = time.time()
                data, mime, _ = load_image(args.image, cfg.max_image_dim)
                prompt = build_prompt("general", "Briefly describe this image in 30 words.", "en")
                provider = make_provider(cfg)
                text = provider.describe([ImagePart(data=data, mime=mime)], prompt)
                elapsed = time.time() - t0
                print(f"  ok       responded in {elapsed:.1f}s, {len(text)} chars")
                print(f"           preview: {text[:140]!r}")
            except Exception as exc:
                print(f"  fail     {exc}")
                ok = False

    print("\n" + "=" * 50)
    print("RESULT:", "ALL GOOD" if ok else "ISSUES FOUND")
    return 0 if ok else 1


# --------------------------- entry ---------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mcp-eyes",
        description="mcp-eyes CLI: bootstrap, configure, and verify an mcp-eyes deployment.",
    )
    parser.add_argument("--version", action="version", version=f"mcp-eyes {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # init
    p_init = sub.add_parser("init", help="Generate CLAUDE.md / AGENTS.md snippet for a project.")
    p_init.add_argument("--reasoning-model", default="", help="Optional. The text reasoning model that calls mcp-eyes. The installing agent already knows its own model and can fill this in for a slightly more polished doc; leave blank for a model-agnostic snippet that works the same way.")
    p_init.add_argument("--lang", choices=("zh", "en"), default="zh")
    p_init.add_argument("--out", default="-", help="Output path; '-' for stdout.")
    p_init.set_defaults(func=cmd_init)

    # presets
    p_pre = sub.add_parser("presets", help="List built-in provider presets.")
    p_pre.add_argument("--format", choices=("json", "table"), default="table")
    p_pre.set_defaults(func=cmd_presets)

    # config
    p_cfg = sub.add_parser("config", help="Generate a .mcp.json server entry.")
    p_cfg.add_argument("--preset", help="Provider preset name (run 'mcp-eyes presets' to see all). If omitted, --protocol/--base-url/--model are required.")
    p_cfg.add_argument("--api-key", required=True, help="Vision provider API key.")
    p_cfg.add_argument("--model", default="", help="Vision model identifier. With --preset, overrides the preset's default_model. Without --preset, this is required.")
    p_cfg.add_argument("--protocol", choices=("openai", "anthropic"), default="openai")
    p_cfg.add_argument("--base-url", default="", help="API base URL (no trailing /chat/completions or /messages).")
    p_cfg.add_argument("--server-name", default="eyes", help="Key under mcpServers (default: eyes).")
    p_cfg.add_argument("--python", default="", help="Python executable path to embed in the config (default: current interpreter).")
    p_cfg.add_argument("--out", default="-", help="Output path; '-' for stdout. Use a project-local .mcp.json or your client's config file.")
    p_cfg.add_argument("--merge", action="store_true", help="If --out exists, merge the new server entry into its mcpServers block instead of overwriting.")
    p_cfg.set_defaults(func=cmd_config)

    # doctor
    p_doc = sub.add_parser("doctor", help="Self-check the current mcp-eyes setup.")
    p_doc.add_argument("--image", default="", help="Optional path/URL to a small test image for a real API ping.")
    p_doc.add_argument("--skip-api", action="store_true", help="Skip the live API ping step.")
    p_doc.set_defaults(func=cmd_doctor)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
