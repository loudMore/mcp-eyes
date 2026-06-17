---
name: install-mcp-eyes
description: Use this skill when the user asks to install or set up mcp-eyes, give their text-only reasoning model vision capability, attach a vision model to their agent, or pastes a GitHub link containing 'mcp-eyes' (https://github.com/loudMore/mcp-eyes). Walks the user through a fully automated install using the mcp-eyes CLI subcommands (presets, config, init, doctor) so no JSON is hand-written. The user only needs to provide the vision API key (and optionally pick a provider).
---

# install-mcp-eyes

You are helping the user install [mcp-eyes](https://github.com/loudMore/mcp-eyes) — an MCP server that gives text-only reasoning LLMs the ability to see images, by routing image inputs to a configured vision model that's locked into description-only mode.

**You ARE the reasoning model that will call mcp-eyes.** You don't need to ask the user what model is calling — that's you.

## What you need from the user (minimum)

1. **Vision API key** (required — only thing they MUST provide)
2. **Provider** (optional — if they don't say, ask once with the short list)

Everything else (base URLs, model names, protocols, prompt templates) is automated.

## The 7-step install flow

### Step 1 — install the package

```bash
pip install git+https://github.com/loudMore/mcp-eyes.git
```

Optional: append `[resize]` for Pillow-based auto-resize of large images:
```bash
pip install "mcp-eyes[resize] @ git+https://github.com/loudMore/mcp-eyes.git"
```

Verify: `python -m mcp_eyes --version` should print `mcp-eyes <version>`.

### Step 2 — pick a vision provider

If the user didn't say which, ask them with this short menu:

> Which vision model? Common picks:
> - `doubao` (火山豆包, 国内快/便宜, OpenAI 协议)
> - `openai` (gpt-4o-mini, 全球, 性价比高)
> - `qwen` (通义千问)
> - `gemini` (Google, 有免费额度)
> - `ollama` (本地, 免费, 无需 API key)
>
> Other providers also supported (`zhipu`, `moonshot/kimi`, `siliconflow`, `openrouter`, `anthropic/claude`, `deepseek`, `doubao-anthropic`). If your provider isn't listed, just give me a base URL + model name.

The full preset list is available via `python -m mcp_eyes presets --format json` if you need to verify a name or look up details.

### Step 3 — get the API key

Ask the user for the key. Tell them: *"I'll write this only into your local .mcp.json. Make sure that file is .gitignored before pasting if your project is on git."*

Different providers prefix keys differently — `ark-…` (Volcano), `sk-…` (OpenAI/Qwen/Moonshot/SF), `sk-ant-…` (Anthropic), `AIza…` (Gemini), arbitrary string for Ollama.

### Step 4 — write the MCP server config

**Default target**: project-local `.mcp.json` (least invasive). Other clients use different paths:

| Client | Config path |
|---|---|
| Claude Code (project) | `<project>/.mcp.json` |
| Claude Code (user) | `~/.claude.json` |
| Cursor | `~/.cursor/mcp.json` |
| Cline | `~/Documents/Cline/MCP/cline_mcp_settings.json` |
| Continue | `~/.continue/config.json` |

Generate with a preset:

```bash
python -m mcp_eyes config \
  --preset doubao \
  --api-key "<USER_KEY>" \
  --merge \
  --out .mcp.json
```

Custom (provider not in presets):

```bash
python -m mcp_eyes config \
  --protocol openai \
  --base-url "https://my.gateway/v1" \
  --model "internal-vision-v2" \
  --api-key "<KEY>" \
  --merge \
  --out .mcp.json
```

Useful flags: `--merge` (preserve other MCP servers in the file), `--server-name <x>` (default `eyes`), `--model <x>` (override preset's default model), `--python <path>` (pin a Python interpreter).

### Step 5 — generate the project's CLAUDE.md snippet

Tells future agents in this project that vision is available and how to use it correctly. The default snippet is **model-agnostic** — you don't need to ask the user what reasoning model you are.

```bash
# Inline the env vars from the config you just wrote:
MCP_EYES_PROTOCOL=openai \
MCP_EYES_BASE_URL="<from-step-4>" \
MCP_EYES_MODEL="<from-step-4>" \
  python -m mcp_eyes init --lang zh --out CLAUDE.md.eyes-section
```

Then append `CLAUDE.md.eyes-section` to the project's existing `CLAUDE.md` (or rename it to `CLAUDE.md` if none exists). **Don't overwrite a long pre-existing CLAUDE.md** — insert under a section header near the top.

If the user wants their specific reasoning model named in the doc, add `--reasoning-model "<your-model-name>"`. Cosmetic only.

### Step 6 — verify

```bash
python -m mcp_eyes doctor --skip-api
```

Expect `RESULT: ALL GOOD`.

If the user can supply a small test image, do the live API ping:

```bash
python -m mcp_eyes doctor --image "<path-to-some.png>"
```

This sends a real request and confirms the API key + URL + model all work end-to-end.

### Step 7 — restart the MCP client

Tell the user:

> Done. Please **restart your MCP client** (Claude Code / Cursor / etc.) so it loads the new `eyes` server. After restart, three tools will be available:
> - `mcp__eyes__describe_image(image, question?, scene?)`
> - `mcp__eyes__compare_images(images[], question?)`
> - `mcp__eyes__extract_text(image)`

Confirm by asking the user to paste any screenshot path. Successful invocation of `mcp__eyes__describe_image` is the success signal.

## Hard rules

- **Never hand-write `.mcp.json`** — always use `mcp-eyes config`. URLs are easy to typo.
- **Never duplicate the prompt protocol** in the user's CLAUDE.md from scratch — it lives on the server in `prompts.py`. The CLAUDE.md snippet only documents *how to call* the tools.
- **Always remind the user to .gitignore .mcp.json** when it contains a real API key.
- **Don't ask the user about**: `MCP_EYES_LANG`, `MCP_EYES_MAX_IMAGE_DIM`, `MCP_EYES_CACHE_ENABLED`, `MCP_EYES_TIMEOUT`, `MCP_EYES_TEMPERATURE` — sensible defaults exist; only surface them if the user asks to tune.

## When something fails

| Symptom | Fix |
|---|---|
| `MCP_EYES_API_KEY is required` at startup | Re-run `mcp-eyes config`, restart client |
| `Vision API error 401` | Wrong key or wrong base_url; verify with `doctor --image` |
| `Vision API error 404` | Model name typo; pass `--model <correct>` and re-run config |
| `Image not found` | Use absolute paths with forward slashes on Windows |
| Tools don't appear | Client not restarted, or config in wrong file (see table in Step 4) |
| Description too short / wrong | Re-call with `bypass_cache: true` and a more specific question, or change `scene` |

## Switching providers later

The user can switch the vision backend any time without touching the project. Just re-run `mcp-eyes config` with a different `--preset` (or `--protocol`/`--base-url`/`--model`) and restart the client. The eyes-only contract is identical across providers.
