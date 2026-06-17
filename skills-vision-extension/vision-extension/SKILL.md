---
name: vision-extension
description: Use this skill for ANY interaction with vision-extension (the open-source vision pack at github.com/loudMore/vision-extension, containing the vision-extension MCP server) — installing/configuring it, calling its tools (`mcp__vision-extension__describe_image`, `mcp__vision-extension__compare_images`, `mcp__vision-extension__extract_text`), or working through tasks where the user gives you a local image path or http(s) image URL while the `vision-extension` MCP server is available. Triggers include: "install vision-extension", "give your model vision", pasting the github.com/loudMore/vision-extension URL, any image path (.png/.jpg/.jpeg/.webp/.gif/.bmp), screenshots, error dialogs, UI mockups, hand-drawn UI sketches, diagrams, charts/dashboards, code screenshots, game frames, annotated bug reports, before/after comparisons, handwritten notes or equations. The skill covers both the install playbook AND the day-to-day collaboration patterns between you (the reasoning model) and the describe-only vision model — picking the right scene, writing question strings the vision model can answer, multi-image batching, cost/cache awareness, error recovery, persona-specific patterns (game devs, frontend, designers, data analysts, QA, educators), and when NOT to call vision-extension.
---

# vision-extension — full lifecycle skill

[`vision-extension`](https://github.com/loudMore/vision-extension) is a pack of two components:

- **`mcp-vision-extension/`** — an MCP server (Python package `vision_extension`) that gives **text-only reasoning models** (you) the ability to see images via a configured vision model.
- **`skills-vision-extension/`** — this skill itself, packaging install + daily-use rules.

The vision model behind the MCP is locked into **description-only mode** server-side: it will not give advice, opinions, hypotheses, or follow-up questions. All thinking, diagnosis, and synthesis is **your** job.

This skill covers everything from "user wants to install" to "user pastes their 100th screenshot today". Pick the relevant section.

---

## PART A — INSTALL & CONFIGURE

Trigger phrases: *"install vision-extension"*, *"set up vision"*, *"give your model vision"*, pasting `github.com/loudMore/vision-extension`.

**You ARE the reasoning model that will call vision-extension** — you don't need to ask the user what model is calling. From the user, you only need: a **vision API key** (and optionally which provider).

### A.1 — install the package

```bash
pip install "git+https://github.com/loudMore/vision-extension.git#subdirectory=mcp-vision-extension"
# Optional: include Pillow for auto-resize of large images
pip install "vision-extension[resize] @ git+https://github.com/loudMore/vision-extension.git#subdirectory=mcp-vision-extension"
```

Verify: `python -m vision_extension --version`. (The Python package is `vision_extension` for ergonomic CLI: `python -m vision_extension init / presets / config / doctor`. The repo and directory are named `vision-extension` for clarity.)

### A.2 — pick a vision provider

Ask the user once with this short menu (don't go into base URLs / model IDs — `vision-extension config` handles those):

> Which vision model? Common picks:
> - `doubao` (火山豆包, 国内快/便宜, OpenAI 协议)
> - `openai` (gpt-4o-mini, 性价比高)
> - `qwen` (通义千问)
> - `gemini` (Google, 有免费额度)
> - `ollama` (本地, 免费, 无需 key)
>
> 也支持: `zhipu`, `moonshot/kimi`, `siliconflow`, `openrouter`, `anthropic/claude`, `deepseek`, `doubao-anthropic`. 不在列表里的话给我 base URL + 模型名即可。

For the full preset table: `python -m vision_extension presets --format json`.

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
python -m vision_extension config --preset doubao --api-key "<KEY>" --merge --out .mcp.json
```

Or with a custom endpoint (provider not in presets):
```bash
python -m vision_extension config --protocol openai --base-url "https://my.gateway/v1" --model "internal-vision" --api-key "<KEY>" --merge --out .mcp.json
```

Useful flags: `--merge` (preserve other MCP servers), `--server-name` (default `vision-extension`), `--model` (override preset's default), `--python` (pin Python interpreter).

### A.5 — generate the project's CLAUDE.md snippet

```bash
VISION_EXTENSION_PROTOCOL=openai \
VISION_EXTENSION_BASE_URL="<from-step-A.4>" \
VISION_EXTENSION_MODEL="<from-step-A.4>" \
  python -m vision_extension init --lang zh --out CLAUDE.md.vision-section
```

Then **append** to existing `CLAUDE.md` (don't overwrite a long pre-existing one — insert under a new section header near the top). Default snippet is model-agnostic; pass `--reasoning-model "<name>"` only if cosmetic naming is wanted.

### A.6 — verify

```bash
python -m vision_extension doctor --skip-api          # env vars + boot
python -m vision_extension doctor --image "<test.png>"  # live API ping
```

Expect `RESULT: ALL GOOD`.

### A.7 — restart MCP client

Tell the user: *"Restart your MCP client so it loads the `vision-extension` server. After restart you'll have `mcp__vision-extension__describe_image`, `mcp__vision-extension__compare_images`, `mcp__vision-extension__extract_text`."*

### A — install hard rules

- **Never hand-write `.mcp.json`** — always use `vision-extension config`. URLs are easy to typo.
- **Never duplicate the prompt protocol** in the user's CLAUDE.md from scratch — it lives on the server in `prompts.py`. The CLAUDE.md snippet only documents *how to call* the tools.
- **Always remind the user to `.gitignore` `.mcp.json`** when it contains a real API key.
- **Don't ask the user about**: `VISION_EXTENSION_LANG`, `VISION_EXTENSION_MAX_IMAGE_DIM`, `VISION_EXTENSION_CACHE_ENABLED`, `VISION_EXTENSION_TIMEOUT`, `VISION_EXTENSION_TEMPERATURE` — defaults are fine; only surface them if the user wants to tune.

---

## PART B — DAILY USE (collaboration with the vision model)

Trigger phrases: any time you're about to call `mcp__vision-extension__*`, or the user gave you an image path/URL while `vision-extension` is available.

### B.1 — quick decision tree

```
Image input arrives:
├─ Single image path/URL?            → mcp__vision-extension__describe_image
├─ Multiple images, asking compare?  → mcp__vision-extension__compare_images
├─ Need ONLY raw text from image?    → mcp__vision-extension__extract_text  (cheaper)
├─ Same image already described in this conversation?
│                                     → DO NOT recall — reuse prior description
└─ User describing image in words (not sending one)?
                                      → DO NOT call vision-extension — no image to look at
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
| **Plot / graph / dashboard panel / data viz (matplotlib, Grafana, Tableau)** | **`chart`** |
| **Handwritten notes / math equations / whiteboard scribbles** | **`handwriting`** |
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
- **Reading data off a chart/dashboard**: `describe_image` (scene=chart) → get axis labels, tick values, series, trends → run the analysis yourself; never ask the vision model "what does this trend mean".
- **Transcribing handwritten notes / math**: `describe_image` (scene=handwriting) → get verbatim text + LaTeX for equations → you do the typesetting / problem solving.

### B.4a — common user personas (and the right scene for each)

When you can identify the user's professional context from their phrasing, the scene + question pattern often follows directly:

| User signal | Scene | Question pattern |
|---|---|---|
| **Game dev** circles a glitch in gameplay screenshot ("这里穿模了 / UI 错位了") | `annotated` | "Describe each circled region: position, what's there, any visible text. Note differences from surrounding area." |
| **Game dev** sends a frame and asks about HUD numbers / enemy count / state | `game` | "Read every HUD value verbatim. Count enemies. Identify visual anomalies (clipping, missing textures shown as pink/black)." |
| **Frontend dev** with a UI bug screenshot, red circles around the breakage | `annotated` | "Describe each annotated region: element type, current visual state, any text in or near it." |
| **Designer** sends Figma export / paper sketch / whiteboard photo | `mockup` | "Reconstruction-grade description so I can rebuild this in <stack>." |
| **Data analyst** sends Grafana panel / chart / Excel plot | `chart` | "List axis labels, full tick values, every series with its trend, and any annotation lines." |
| **DevOps / SRE** sends a multi-panel dashboard | `chart` | "For each dashboard panel: title, primary number/state, color." |
| **QA tester** sends an annotated bug repro screenshot | `annotated` | "Describe each annotation in repro order; transcribe error text verbatim." |
| **Educator / student** sends handwritten notes or equations | `handwriting` | "Transcribe verbatim; render math as LaTeX; flag uncertain characters." |
| **Localization worker** sends UI screenshots for translation | `ui` | "List every visible string verbatim with its UI position. Flag text inside images vs editable text." |
| **Researcher** sends paper screenshot with chart + text | `general` (or split into `ocr` + `chart`) | "Transcribe the paragraph + describe the chart structurally." |
| **Hardware / maker** sends circuit / schematic / oscilloscope photo | `diagram` | "List every component label, connection, and reading verbatim." |
| **PM / business** sends competitor app screenshot for feature analysis | `ui` | "Enumerate every UI element with its position and apparent function." |

If the persona doesn't match exactly, fall back to keyword-based `auto` or pick the closest scene from B.2.

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
| `vision call failed: 401` | API key wrong; tell user to re-run `vision-extension config` |
| `vision call failed: 404` | Model name wrong; check `vision-extension presets` |
| `Image not found` | Bad path — confirm with user, use absolute forward-slash paths on Windows |

### B.8 — when NOT to call vision-extension

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

> **Install once with the CLI, never hand-write JSON. Then: the vision model is your sensor, not your brain. Use it to *see*, then *think* yourself. Ask it *what is there*, never *what to do*. Pick the right `scene`, write a precise `question`, and reuse cached descriptions instead of re-asking.**
