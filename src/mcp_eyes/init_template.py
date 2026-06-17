"""Initialization helper.

`python -m mcp_eyes init` prints a CLAUDE.md / AGENTS.md snippet that documents
how the local agent should use mcp-eyes. It auto-fills the configured vision
model + protocol from the environment. The reasoning model is a placeholder
the integrator overrides via --reasoning-model, since the server has no way
to know which text model is calling it.
"""

from __future__ import annotations

import argparse
import os
import sys

TEMPLATE_ZH = """## 视觉识图 (mcp-eyes)

**主模型 `{reasoning_model}` 是纯文本推理模型，无法直接识别图片。**

本项目通过 MCP server `eyes`（[mcp-eyes](https://github.com/loudMore/mcp-eyes)）把视觉能力外挂给主模型。当前配置：

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
3. **视觉模型已在服务端被锁成"eyes-only"**：不会给修复建议、不会推测原因、不会反问 —— 只做客观描述和逐字转录。所以推理、诊断、修复方案都由我（主模型 `{reasoning_model}`）来做，不要让视觉模型回答 "为什么 / 怎么修 / 哪里有问题"。
4. **`scene` 参数怎么选**：默认 `auto` 按问题关键词识别。手动可选 `general / annotated / ui / error / code / game / webpage / chat / terminal / diagram / comparison / table / lowquality / ocr`。
5. **`question` 怎么写**：问"看到什么"，别问"该怎么办"。
   - ✅ "逐字转录报错堆栈，含文件路径和行号"
   - ✅ "图中红圈圈出的是什么？"
   - ❌ "为什么会报这个错？"（视觉模型不会回答）
6. **结果是数据不是答案**：拿到描述后由我自己分析、综合，再回答用户。

### 缓存

同一张图 + 同一个 `question` + 同一个 `scene` + 同一个模型 = 命中本地缓存，零成本。要强制重调用传 `bypass_cache: true`。
"""

TEMPLATE_EN = """## Vision via mcp-eyes

**The reasoning model `{reasoning_model}` is text-only and cannot see images.**

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
3. **The vision model is locked into eyes-only mode** server-side: no advice, no opinions, no speculation, no follow-up questions — just verbatim transcription and structured description. Reasoning, diagnosis, and fix suggestions are MY job (the reasoning model `{reasoning_model}`). Never ask the vision model "why" or "how to fix".
4. **Picking `scene`**: default `auto` keyword-detects. Override with one of `general / annotated / ui / error / code / game / webpage / chat / terminal / diagram / comparison / table / lowquality / ocr`.
5. **Writing `question`**: ask what's visible, not what to do.
   - ✅ "Transcribe the stack trace verbatim, including file paths and line numbers."
   - ✅ "What does the red-circled element show?"
   - ❌ "Why is this failing?" — the vision model will refuse this part.
6. **The output is data, not the final answer**: synthesize and respond to the user from the description, don't forward it raw.

### Caching

Same image + same `question` + same `scene` + same model = local cache hit, zero cost. Pass `bypass_cache: true` to force a fresh call.
"""


def _vars_from_env(reasoning_model: str) -> dict[str, str]:
    return {
        "reasoning_model": reasoning_model or "<your-reasoning-model>",
        "protocol": os.environ.get("MCP_EYES_PROTOCOL", "<not-set>"),
        "vision_model": os.environ.get("MCP_EYES_MODEL", "<not-set>"),
        "base_url": os.environ.get("MCP_EYES_BASE_URL", "<not-set>"),
    }


def render(reasoning_model: str, lang: str) -> str:
    template = TEMPLATE_ZH if lang == "zh" else TEMPLATE_EN
    return template.format(**_vars_from_env(reasoning_model))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mcp-eyes init",
        description="Print a CLAUDE.md / AGENTS.md snippet for integrating mcp-eyes into a project.",
    )
    parser.add_argument(
        "--reasoning-model",
        default="",
        help="Name of the text reasoning model the agent uses (e.g. glm-5.2, deepseek-v4-pro, claude-sonnet-4-5, gpt-4o, kimi-k2). This is the model that will CALL mcp-eyes — it cannot be auto-detected.",
    )
    parser.add_argument(
        "--lang",
        choices=("zh", "en"),
        default="zh",
        help="Output language (default: zh).",
    )
    parser.add_argument(
        "--out",
        default="-",
        help="Output file (default: stdout). Use '-' for stdout.",
    )
    args = parser.parse_args(argv)

    snippet = render(args.reasoning_model, args.lang)

    if args.out == "-":
        try:
            sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except Exception:
            pass
        try:
            sys.stdout.write(snippet)
            sys.stdout.flush()
        except UnicodeEncodeError:
            sys.stdout.buffer.write(snippet.encode("utf-8"))
            sys.stdout.buffer.flush()
    else:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(snippet)
        print(f"wrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
