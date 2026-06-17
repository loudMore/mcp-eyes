---
name: mcp-eyes
description: Use this skill for ANY interaction with mcp-eyes — installing/configuring it, calling its tools (`mcp__eyes__describe_image`, `mcp__eyes__compare_images`, `mcp__eyes__extract_text`), or working through tasks where the user gives you a local image path or http(s) image URL while the `eyes` MCP server is available. Triggers include: "install mcp-eyes", "give you eyes / vision", pasting the github.com/loudMore/mcp-eyes URL, any image path (.png/.jpg/.jpeg/.webp/.gif/.bmp), screenshots, error dialogs, UI mockups, diagrams, code screenshots, game frames, annotated images, before/after pairs. The skill covers both the install playbook AND the day-to-day collaboration patterns between you (the reasoning model) and the eyes-only vision model — picking the right scene, writing question strings the vision model can answer, multi-image batching, cost/cache awareness, error recovery, and when NOT to call mcp-eyes.
---

# mcp-eyes — full lifecycle skill

mcp-eyes is an MCP server that gives **text-only reasoning models** (you) the ability to see images by routing them to a configured vision model. The vision model is locked into **description-only mode** server-side: it will not give advice, opinions, hypotheses, or follow-up questions. All thinking, diagnosis, and synthesis is **your** job.

This skill covers everything from "user wants to install" to "user pastes their 100th screenshot today". Pick the relevant section.

---

## PART A — INSTALL & CONFIGURE

Trigger phrases: *"install mcp-eyes"*, *"set up vision"*, *"give you eyes"*, pasting `github.com/loudMore/mcp-eyes`.

**You ARE the reasoning model that will call mcp-eyes** — you don't need to ask the user what model is calling. From the user, you only need: a **vision API key** (and optionally which provider).

### A.1 — install the package

```bash
pip install git+https://github.com/loudMore/mcp-eyes.git
# Optional: include Pillow for auto-resize of large images
pip install "mcp-eyes[resize] @ git+https://github.com/loudMore/mcp-eyes.git"
```

Verify: `python -m mcp_eyes --version`.

### A.2 — pick a vision provider

Ask the user once with this short menu (don't go into base URLs / model IDs — `mcp-eyes config` handles those):

> Which vision model? Common picks:
> - `doubao` (火山豆包, 国内快/便宜, OpenAI 协议)
> - `openai` (gpt-4o-mini, 性价比高)
> - `qwen` (通义千问)
> - `gemini` (Google, 有免费额度)
> - `ollama` (本地, 免费, 无需 key)
>
> 也支持: `zhipu`, `moonshot/kimi`, `siliconflow`, `openrouter`, `anthropic/claude`, `deepseek`, `doubao-anthropic`. 不在列表里的话给我 base URL + 模型名即可。

For the full preset table: `python -m mcp_eyes presets --format json`.

### A.3 — get the API key

Tell user: *"I'll write this only into your local .mcp.json. Make sure that file is .gitignored before pasting if your project is on git."*

Key prefixes vary by provider: `ark-…` (火山), `sk-…` (OpenAI/Qwen/Moonshot/SF), `sk-ant-…` (Anthropic), `AIza…` (Gemini), arbitrary string (Ollama).

### A.4 — write the MCP server config

**Default target**: project-local `.mcp.json` (least invasive). Other clients use:

| Client | Config path |
|---|---|
| Claude Code (project) | `<project>/.mcp.json` |
| Claude Code (user) | `~/.claude.json` |
| Cursor | `~/.cursor/mcp.json` |
| Cline | `~/Documents/Cline/MCP/cline_mcp_settings.json` |
| Continue | `~/.continue/config.json` |

Generate with a preset:
```bash
python -m mcp_eyes config --preset doubao --api-key "<KEY>" --merge --out .mcp.json
```

Or with a custom endpoint (provider not in presets):
```bash
python -m mcp_eyes config --protocol openai --base-url "https://my.gateway/v1" --model "internal-vision" --api-key "<KEY>" --merge --out .mcp.json
```

Useful flags: `--merge` (preserve other MCP servers), `--server-name` (default `eyes`), `--model` (override preset's default), `--python` (pin Python interpreter).

### A.5 — generate the project's CLAUDE.md snippet

```bash
MCP_EYES_PROTOCOL=openai \
MCP_EYES_BASE_URL="<from-step-A.4>" \
MCP_EYES_MODEL="<from-step-A.4>" \
  python -m mcp_eyes init --lang zh --out CLAUDE.md.eyes-section
```

Then **append** to existing `CLAUDE.md` (don't overwrite a long pre-existing one — insert under a new section header near the top). Default snippet is model-agnostic; pass `--reasoning-model "<name>"` only if cosmetic naming is wanted.

### A.6 — verify

```bash
python -m mcp_eyes doctor --skip-api          # env vars + boot
python -m mcp_eyes doctor --image "<test.png>"  # live API ping
```

Expect `RESULT: ALL GOOD`.

### A.7 — restart MCP client

Tell the user: *"Restart your MCP client so it loads the `eyes` server. After restart you'll have `mcp__eyes__describe_image`, `mcp__eyes__compare_images`, `mcp__eyes__extract_text`."*

### A — install hard rules

- **Never hand-write `.mcp.json`** — always use `mcp-eyes config`. URLs are easy to typo.
- **Never duplicate the prompt protocol** in the user's CLAUDE.md from scratch — it lives on the server in `prompts.py`. The CLAUDE.md snippet only documents *how to call* the tools.
- **Always remind the user to `.gitignore` `.mcp.json`** when it contains a real API key.
- **Don't ask the user about**: `MCP_EYES_LANG`, `MCP_EYES_MAX_IMAGE_DIM`, `MCP_EYES_CACHE_ENABLED`, `MCP_EYES_TIMEOUT`, `MCP_EYES_TEMPERATURE` — defaults are fine; only surface them if the user wants to tune.

---

## PART B — DAILY USE (collaboration with the vision model)

Trigger phrases: any time you're about to call `mcp__eyes__*`, or the user gave you an image path/URL while `eyes` is available.

### B.1 — quick decision tree

```
Image input arrives:
├─ Single image path/URL?            → mcp__eyes__describe_image
├─ Multiple images, asking compare?  → mcp__eyes__compare_images
├─ Need ONLY raw text from image?    → mcp__eyes__extract_text  (cheaper)
├─ Same image already described in this conversation?
│                                     → DO NOT recall — reuse prior description
└─ User describing image in words (not sending one)?
                                      → DO NOT call mcp-eyes — no image to look at
```

### B.2 — pick the right `scene`

`scene="auto"` is fine when the question contains obvious keywords. Override explicitly when you can:

| Situation | scene |
|---|---|
| Red circles, arrows, highlights, batch annotations | `annotated` |
| Software UI / form / dashboard | `ui` |
| **User's hand-drawn UI sketch / wireframe / mockup that they want reproduced as code** | **`mockup`** |
| Error dialog, IDE/console exception, traceback | `error` |
| Editor / GitHub / web code block | `code` |
| Running game frame (HUD, enemies, particles) | `game` |
| Browser page (article, doc, SO answer) | `webpage` |
| WeChat/Discord/Slack/iMessage screenshot | `chat` |
| Terminal / shell output | `terminal` |
| Flowchart, architecture, wireframe (informational, not for reproduction) | `diagram` |
| Side-by-side or before/after | `comparison` |
| Spreadsheet / data table | `table` |
| Blurry / dark / compressed | `lowquality` |
| Pure text extraction, no analysis | `ocr` |
| Nothing fits | `general` |

#### 🎯 The `mockup` scene is the high-value one

When a user sends a screenshot or photo of a **UI design** (Figma, Photoshop, paper sketch, whiteboard, napkin drawing, prototyping app) and says something like *"build this in Godot"* / *"implement this in HTML/CSS"* / *"make this UI"* / *"复刻这个界面"*:

- **Use `scene="mockup"`**. The vision model will produce a *reconstruction-grade* description: layout grid in percentages, every element's type/text/shape/size/position, hierarchy, all colors, typography hints, spacing, connectors, state indicators, and any handwritten annotations.
- **Then YOU (the reasoning model) write the code** from that description alone. No need to see the image yourself.
- Example invocation:
  ```
  describe_image(
    image="C:/Users/dev/whiteboard_mockup.jpg",
    scene="mockup",
    question="复刻这个 UI 到 Godot Control 节点树，所有文字保留中文原文，颜色按描述就近匹配 Godot 主题"
  )
  ```
- After the description comes back, generate the actual Godot scene / HTML / Flutter widget from it. **Do not** ask the vision model to write the code — it can't and won't. That part is yours.

### B.3 — writing `question` strings

The vision model answers **what** and **where**, not **why** and **how**.

**Good patterns:**

> "Transcribe the error stack VERBATIM, including file paths, line numbers, and 'Caused by' chains. Preserve line breaks."

> "What does the element circled in red show? Transcribe any text on or near it."

> "List every menu item in the toolbar, left to right, exactly as written."

> "Read the HP and energy values in the top-left HUD."

> "Is there a red error indicator anywhere? If yes, where, and what text is next to it?"

**Anti-patterns** (vision model will refuse and reply "Not visible in image"):

| ❌ Don't ask | ✅ Ask instead |
|---|---|
| "Why is this error happening?" | "Transcribe the error verbatim." (then YOU diagnose) |
| "How do I fix this UI bug?" | "Describe the visual anomaly: position, color, surroundings." |
| "Is this design good?" | "List every UI element with position and color." |
| "Suggest improvements" | (don't ask — vision model is not allowed to opine) |
| "What should I do next?" | (your job, not its job) |

### B.4 — multi-step workflows

Complex tasks need **one vision call to gather, then your own reasoning to act.**

- **User wants UI reproduced from a screenshot/sketch**: `describe_image` (scene=`mockup`) → write the Godot scene / HTML / Flutter / SwiftUI / React from the description alone. The mockup scene is specifically engineered to produce reconstruction-grade output. Don't ask the vision model "is this layout good" — that's banned by role lock and useless anyway. Just take the description and code it up.
- **Debugging from a screenshot**: `describe_image` (scene=error) → match stack against codebase → propose fix. Don't call vision again to "validate".
- **UI regression**: `describe_image` (scene=ui) → diff against intended design (read the code) → propose changes → optionally `compare_images` of before/after after the fix.
- **Game balancing from a frame**: `describe_image` (scene=game) → extract HP/energy/score numbers → plug into formulas yourself.
- **Reading code from a screenshot before editing**: `extract_text` is enough → reconstruct in context → find the file in the project → edit the file directly.

### B.5 — multi-image strategy

- **2–6 images, same context**: one `compare_images` call. Order matters — pass them in the order to be compared.
- **7+ images**: batch into chunks of 6.
- **Animation/sequence frames**: name them `frame_01.png`, `frame_02.png` so the vision model can reference by index.
- **Same image, multiple questions**: ask one well-crafted compound question. Each call is a separate API charge.

### B.6 — cost / cache awareness

| Action | Effect |
|---|---|
| Same `image + question + scene + model` | **Cache hit, 0 cost** |
| Same image, different question | New API call, full cost |
| Compare 4 images in one call | One charge with bigger payload — much faster than 4 calls |
| Image >5 MB without Pillow | Slow upload, may truncate — suggest user crop |
| Calling vision twice to "double-check" | Wasted money. The first answer is what the model saw. |

Pass `bypass_cache: true` only when the file actually changed.

### B.7 — error recovery

| Vision returned… | Do this |
|---|---|
| "Not visible in image" for a part | Re-ask as "what is at location X" / ask user to circle |
| Description shorter than expected | Pick a more specific `scene`; ask for structured enumeration |
| Garbled / mixed-language transcription | Image too small — ask for higher-res screenshot |
| `vision call failed: 401` | API key wrong; tell user to re-run `mcp-eyes config` |
| `vision call failed: 404` | Model name wrong; check `mcp-eyes presets` |
| `Image not found` | Bad path — confirm with user, use absolute forward-slash paths on Windows |

### B.8 — when NOT to call mcp-eyes

- User is **describing** an image in words (not sending one). Reason from their description.
- Image was **already described earlier** in this conversation. Reuse — don't pay twice.
- User pasted **text that came from an image** (manual OCR transcript). Work with the text.
- Image is a **logo / brand mark** the user obviously knows. Skip the obvious description.
- Task is **purely about code/text already typed in chat**, screenshot is supplementary. Chat text is canonical.

### B.9 — output handling

The vision model returns **structured description, not a final answer**. After the call:

1. **Synthesize** — combine description + codebase reads + prior context + the user's actual question.
2. **Don't echo** — never paste raw vision output back to the user as your reply unless they explicitly asked for a transcript.
3. **Don't translate verbatim transcriptions** — stack traces, code, error codes stay in their original language.
4. **Cite spatial references** — use the vision model's positions ("the red-circled button at top-right"), not pixel coordinates.

---

## One-line summary

> **Install once with the CLI, never hand-write JSON. Then: the vision model is your eyes, not your brain. Use it to *see*, then *think* yourself. Ask it *what is there*, never *what to do*. Pick the right `scene`, write a precise `question`, and reuse cached descriptions instead of re-asking.**
