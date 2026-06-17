# AGENT_SETUP.md — installation playbook for AI agents

> **Audience**: An AI coding agent (Claude Code / Cursor / Cline / Continue / Roo / etc.) whose user just asked to install mcp-eyes from `https://github.com/loudMore/mcp-eyes`. Follow these steps. They are designed so the user only has to provide their **vision API key** (and optionally a provider name); everything else is automated.

---

## TL;DR for the agent

```
1. pip install git+https://github.com/loudMore/mcp-eyes.git
2. Ask user: "Which vision provider?" → look up in presets
3. Ask user: "Paste your API key for <provider>"
4. mcp-eyes config --preset <name> --api-key <key> --merge --out <client-config-path>
5. Ask user: "Which reasoning model are YOU running this agent on?"
6. mcp-eyes init --reasoning-model "<that-model>" --lang <zh|en> --out <project>/CLAUDE.md.eyes
7. Tell user to paste the snippet into their CLAUDE.md (or do it for them if they say so)
8. mcp-eyes doctor --image <some-test-image>      # verify
9. Tell user to restart their MCP client so `eyes` server gets picked up
```

The four CLI subcommands (`config`, `init`, `presets`, `doctor`) exist precisely so you don't have to hand-write JSON or invent prompt strings. **Use them.**

---

## Step 1 — install the package

The package lives on GitHub, not PyPI (yet). One-liner:

```bash
pip install git+https://github.com/loudMore/mcp-eyes.git
```

Optional: `pip install "mcp-eyes[resize] @ git+https://github.com/loudMore/mcp-eyes.git"` to also install Pillow (auto-resize for large images).

Verify: `python -m mcp_eyes --version` should print `mcp-eyes <version>`.

---

## Step 2 — pick a vision provider (ask the user)

Run `python -m mcp_eyes presets` to see the built-in list. As of writing it covers:

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
python -m mcp_eyes config \
  --preset doubao \
  --api-key "<USER_PROVIDED_KEY>" \
  --merge \
  --out ".mcp.json"
```

Custom path:
```bash
python -m mcp_eyes config \
  --protocol openai \
  --base-url "https://my.gateway/v1" \
  --model "internal-vision-v2" \
  --api-key "<KEY>" \
  --merge \
  --out ".mcp.json"
```

Flags worth knowing:
- `--merge` — if the file already has other MCP servers, keep them; just add `eyes` next to them.
- `--server-name` — change the registered name from `eyes` (e.g. if the user already has another `eyes` server, use `eyes2`).
- `--model` — override the preset's `default_model` (e.g. `--preset openai --model gpt-4o` for higher quality).
- `--python` — pin a specific Python interpreter (matters when the user has multiple installs).

---

## Step 5 — generate the CLAUDE.md / AGENTS.md snippet

**Critical**: the server cannot detect which reasoning model is calling it. The user must tell you.

> **You**: "What reasoning model is running this agent? (e.g. `glm-5.2`, `deepseek-v4-pro`, `claude-sonnet-4-5`, `gpt-4o`, `kimi-k2`)"

Then:

```bash
# Read the env vars you just wrote to .mcp.json so init can fill them in.
# On Linux/macOS:
export $(python -c "import json; d=json.load(open('.mcp.json'))['mcpServers']['eyes']['env']; [print(f'{k}={v}') for k,v in d.items()]")

# Or simpler (and cross-platform): just inline them
MCP_EYES_PROTOCOL=openai \
MCP_EYES_BASE_URL="<from-config>" \
MCP_EYES_MODEL="<from-config>" \
  python -m mcp_eyes init \
    --reasoning-model "<USER_PROVIDED_MODEL>" \
    --lang zh \
    --out CLAUDE.md.eyes-section
```

Then either append `CLAUDE.md.eyes-section` to the project's existing `CLAUDE.md` (or `AGENTS.md`), or — if there's no such file yet — rename it to `CLAUDE.md`.

If the user has a long pre-existing `CLAUDE.md`, **don't overwrite**; insert the snippet near the top under a section header.

---

## Step 6 — verify

```bash
python -m mcp_eyes doctor --skip-api
```

Should print `RESULT: ALL GOOD`.

If the user can supply a small test image, do the live ping too:

```bash
python -m mcp_eyes doctor --image "C:/path/to/anything.png"
```

This sends a real request to the configured provider and confirms the API key + URL + model all work.

---

## Step 7 — restart the MCP client

MCP clients pick up new servers at startup. Tell the user:

> "Done. Please **restart your MCP client** (Claude Code / Cursor / etc.) so it loads the new `eyes` server. After restart, the tools `mcp__eyes__describe_image`, `mcp__eyes__compare_images`, `mcp__eyes__extract_text` will be available to me."

Then to confirm: ask the user to paste a screenshot path. You should see the agent invoke `mcp__eyes__describe_image` — that's the success signal.

---

## What you should NEVER do

- ❌ Don't hand-write `.mcp.json`. Use `mcp-eyes config`. The CLI gets every URL exactly right; you'll typo a base_url.
- ❌ Don't write the prompt protocol into the user's `CLAUDE.md` from scratch. The prompt protocol lives **on the server** in `src/mcp_eyes/prompts.py`. The `CLAUDE.md` snippet only documents how to *call* the tools.
- ❌ Don't commit `.mcp.json` containing a real API key. Always remind the user to `.gitignore` it (or use environment variables and reference `${ENV_VAR}` if their MCP client supports it).
- ❌ Don't ask the user for things you can derive: `MCP_EYES_LANG`, `MCP_EYES_MAX_IMAGE_DIM`, `MCP_EYES_CACHE_ENABLED` — leave them at sensible defaults.
- ❌ Don't add provider presets locally for one user. If a provider is missing from `presets.py`, that's a PR-worthy contribution to the upstream repo.

---

## Troubleshooting (give this to the user when things break)

| Symptom | Likely cause | Fix |
|---|---|---|
| `MCP_EYES_API_KEY is required` at startup | env vars not set | Re-run `mcp-eyes config`, then restart the client |
| `Vision API error 401` | wrong key or wrong base_url | Verify with `mcp-eyes doctor --image <path>` |
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
