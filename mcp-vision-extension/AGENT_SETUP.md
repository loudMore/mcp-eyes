# AGENT_SETUP.md — installation playbook for AI agents

> **Audience**: An AI coding agent (Claude Code / Cursor / Cline / Continue / Roo / etc.) whose user just asked to install vision-extension from `https://github.com/loudMore/vision-extension`. Follow these steps. They are designed so the user only has to provide their **vision API key** (and optionally a provider name); everything else is automated.

---

## TL;DR for the agent

```
1. pip install git+https://github.com/loudMore/vision-extension.git#subdirectory=mcp-vision-extension
2. Ask user: "Which vision provider?" → look up in presets
3. Ask user: "Paste your API key for <provider>"
4. vision-extension config --preset <name> --api-key <key> --merge --out <client-config-path>
5. vision-extension init --lang <zh|en> --out <project>/CLAUDE.md.vision-section
   (You ARE the reasoning model — you don't need to ask the user what model is calling.
    Optional: pass --reasoning-model "<your-own-model-name>" if you want it shown in the doc.)
6. Paste the snippet into the project's CLAUDE.md (top of file, under a header)
7. vision-extension doctor --image <some-test-image>      # verify
8. Tell user to restart their MCP client so `vision-extension` server gets picked up
```

The four CLI subcommands (`config`, `init`, `presets`, `doctor`) exist precisely so you don't have to hand-write JSON or invent prompt strings. **Use them.** And the only thing you actually need from the user is the **vision API key** — everything else you can derive or default.

---

## Step 1 — install the package

The package lives on GitHub, not PyPI (yet). One-liner:

```bash
pip install git+https://github.com/loudMore/vision-extension.git#subdirectory=mcp-vision-extension
```

Optional: `pip install "vision-extension[resize] @ git+https://github.com/loudMore/vision-extension.git#subdirectory=mcp-vision-extension"` to also install Pillow (auto-resize for large images).

Verify: `python -m vision_extension --version` should print `vision-extension <version>`.

---

## Step 2 — pick a vision provider (ask the user)

Run `python -m vision_extension presets` to see the built-in list. As of writing it covers:

`doubao` · `doubao-anthropic` · `openai` · `anthropic` · `qwen` · `zhipu` · `gemini` · `siliconflow` · `openrouter` · `ollama` · `moonshot` · `deepseek`

Aliases are accepted (e.g. `volcano`, `kimi`, `glm`, `claude`, `gpt-4o`, `tongyi`, `豆包`, `通义`, `智谱` …).

### What you must ask the user

> **You**: "Which vision provider do you want to use? Common picks:
> - `doubao` (火山引擎豆包, 国内快/便宜)
> - `openai` (gpt-4o-mini, 全球, 性价比高)
> - `qwen` (通义千问, 阿里)
> - `gemini` (Google, 有免费额度)
> - `ollama` (本地, 免费, 无需 key)
>
> 你的 API 来源不在这上面也可以 — 直接告诉我 base URL 和模型名即可。"

If the user names something that's **not** in `presets`, fall through to **Step 2b**.

### Step 2b — custom / unknown provider

If the user has their own gateway, internal proxy, or a provider not in the preset list, ask for:

1. **Protocol** — `openai` (most common) or `anthropic` (the Claude messages format)
2. **Base URL** — without trailing `/chat/completions` or `/messages`
3. **Model identifier** — exact string the API expects
4. **API key**

Then in **Step 3** you'll skip `--preset` and pass `--protocol --base-url --model` instead.

---

## Step 3 — get the API key

Some providers prefix their keys distinctively (e.g. `ark-…`, `sk-…`, `sk-ant-…`, `AIza…`). The `presets` JSON includes a `key_format_hint` and `key_signup_url` per provider — use them when guiding the user.

**Privacy reminder you should give the user**: "I'll paste this key into your local `.mcp.json` only. Nothing leaves your machine. If your project is git-tracked, make sure `.mcp.json` is `.gitignore`d **before** pasting."

---

## Step 4 — generate the MCP server config

### Where to write it

Different MCP clients store the server list in different places. Common targets:

| Client | Config path |
|---|---|
| Claude Code (project-scoped) | `<project>/.mcp.json` |
| Claude Code (user-scoped) | `~/.claude.json` (under `mcpServers`) |
| Cursor | `~/.cursor/mcp.json` (or `<project>/.cursor/mcp.json`) |
| Cline | `~/Documents/Cline/MCP/cline_mcp_settings.json` |
| Continue | `~/.continue/config.json` |
| Roo Code | `~/.roo/mcp_settings.json` |

If the user doesn't tell you which, **default to project-local `.mcp.json`** — it's least invasive and easiest to revert.

### Generate

Preset path:
```bash
python -m vision_extension config \
  --preset doubao \
  --api-key "<USER_PROVIDED_KEY>" \
  --merge \
  --out ".mcp.json"
```

Custom path:
```bash
python -m vision_extension config \
  --protocol openai \
  --base-url "https://my.gateway/v1" \
  --model "internal-vision-v2" \
  --api-key "<KEY>" \
  --merge \
  --out ".mcp.json"
```

Flags worth knowing:
- `--merge` — if the file already has other MCP servers, keep them; just add `vision-extension` next to them.
- `--server-name` — change the registered name from `vision-extension` (e.g. if the user already has another `vision-extension` server, use `vision-extension2`).
- `--model` — override the preset's `default_model` (e.g. `--preset openai --model gpt-4o` for higher quality).
- `--python` — pin a specific Python interpreter (matters when the user has multiple installs).

---

## Step 5 — generate the CLAUDE.md / AGENTS.md snippet

The `init` command produces a doc block that tells future agents working in this project how to call vision-extension correctly. **You do not need to ask the user which reasoning model is calling vision-extension — you are that reasoning model**, and the default snippet is intentionally model-agnostic anyway.

```bash
# Inline the env vars from the config you just wrote so init can fill them in.
VISION_EXTENSION_PROTOCOL=openai \
VISION_EXTENSION_BASE_URL="<from-config>" \
VISION_EXTENSION_MODEL="<from-config>" \
  python -m vision_extension init \
    --lang zh \
    --out CLAUDE.md.vision-section
```

If you want the snippet to mention your own model name (e.g. for clarity in a single-agent project), add `--reasoning-model "<your-own-name>"` — but it's optional and changes nothing functionally.

Then either append `CLAUDE.md.vision-section` to the project's existing `CLAUDE.md` (or `AGENTS.md`), or rename it if no such file exists yet. Don't overwrite a long pre-existing `CLAUDE.md` — insert under a new section header near the top.

---

## Step 6 — verify

```bash
python -m vision_extension doctor --skip-api
```

Should print `RESULT: ALL GOOD`.

If the user can supply a small test image, do the live ping too:

```bash
python -m vision_extension doctor --image "C:/path/to/anything.png"
```

This sends a real request to the configured provider and confirms the API key + URL + model all work.

---

## Step 7 — restart the MCP client

MCP clients pick up new servers at startup. Tell the user:

> "Done. Please **restart your MCP client** (Claude Code / Cursor / etc.) so it loads the new `vision-extension` server. After restart, the tools `mcp__vision-extension__describe_image`, `mcp__vision-extension__compare_images`, `mcp__vision-extension__extract_text` will be available to me."

Then to confirm: ask the user to paste a screenshot path. You should see the agent invoke `mcp__vision-extension__describe_image` — that's the success signal.

---

## What you should NEVER do

- ❌ Don't hand-write `.mcp.json`. Use `vision-extension config`. The CLI gets every URL exactly right; you'll typo a base_url.
- ❌ Don't write the prompt protocol into the user's `CLAUDE.md` from scratch. The prompt protocol lives **on the server** in `src/vision_extension/prompts.py`. The `CLAUDE.md` snippet only documents how to *call* the tools.
- ❌ Don't commit `.mcp.json` containing a real API key. Always remind the user to `.gitignore` it (or use environment variables and reference `${ENV_VAR}` if their MCP client supports it).
- ❌ Don't ask the user for things you can derive: `VISION_EXTENSION_LANG`, `VISION_EXTENSION_MAX_IMAGE_DIM`, `VISION_EXTENSION_CACHE_ENABLED` — leave them at sensible defaults.
- ❌ Don't add provider presets locally for one user. If a provider is missing from `presets.py`, that's a PR-worthy contribution to the upstream repo.

---

## Troubleshooting (give this to the user when things break)

| Symptom | Likely cause | Fix |
|---|---|---|
| `VISION_EXTENSION_API_KEY is required` at startup | env vars not set | Re-run `vision-extension config`, then restart the client |
| `Vision API error 401` | wrong key or wrong base_url | Verify with `vision-extension doctor --image <path>` |
| `Vision API error 404` | model name typo | Check the provider's docs; pass `--model` to override |
| `vision call failed: Image not found` | bad path | Use absolute paths with forward slashes on Windows |
| Tools don't appear in client | client not restarted, or config in wrong file | Restart; check the right config file (table above) |
| Description is too short / wrong | bad `question` | Re-call with `bypass_cache: true` and a more specific question, or change `scene` |

---

## Customization beyond the preset list

If the user runs an internal proxy or self-hosted vision model that isn't a preset:

1. Skip `--preset`, pass `--protocol / --base-url / --model` directly.
2. Most self-hosted servers (vLLM, LiteLLM proxy, Xinference, LM Studio, OneAPI) speak OpenAI protocol — pick `--protocol openai`.
3. If their endpoint requires custom headers (e.g. a tenant ID), that's currently not exposed via CLI — they'd need to set the env var directly in `.mcp.json` and patch `providers/openai_compat.py`. PRs welcome.

For everything else, follow the playbook above and you're done.
