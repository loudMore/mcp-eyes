# AGENTS.md

> Guidance for AI agents (Claude Code, Cursor, Cline, Continue, custom MCP clients) that read this repo or sit alongside it in a project.

## What this repo is

`mcp-eyes` is a Model Context Protocol (MCP) server. It gives **text-only reasoning LLMs** the ability to see images by routing them to a configured vision model. Crucially, the vision model is locked into description-only mode (the "eyes-only protocol"), so it does not produce advice, hypotheses, opinions, or solutions — only structured visual transcription. Higher-level reasoning is the calling model's job.

## When you (the agent) should call this server's tools

You should invoke `mcp-eyes` tools whenever **any** of the following is true and the `eyes` MCP server is available:

1. The user message references a local image path (`.png .jpg .jpeg .webp .gif .bmp`).
2. The user gives an `http(s)://` URL that resolves to an image.
3. The user pastes a screenshot description, mentions "the screenshot", "this UI", "this error dialog", "the diagram", and an image path is in scope.
4. You need to read text out of an image (OCR).
5. You need to compare two or more images.

Do **not** use generic file-reading tools (`Read`, `cat`, etc.) on image files — they will either fail or feed binary garbage to the text model.

## Tools

### `describe_image`

```json
{
  "image": "C:/path/to/file.png",   // or http(s) URL
  "question": "What does the red-circled element show?",
  "scene": "annotated",             // optional, see scenes below
  "bypass_cache": false             // optional, force a fresh call
}
```

Returns: structured plain text. Treat it as data, not as the final answer to the user.

### `compare_images`

```json
{
  "images": ["C:/before.png", "C:/after.png"],
  "question": "What changed?",
  "scene": "comparison"
}
```

### `extract_text`

```json
{ "image": "C:/path.png" }
```

Pure OCR shortcut.

## Scene presets

Pass `scene` when the question is ambiguous. `auto` infers from the question text.

| Scene | Use when |
|---|---|
| `auto` | Default. Keyword-detected. |
| `general` | No specific structure. |
| `annotated` | User added red circles, arrows, highlights, or notes on the image. |
| `ui` | Software interface screenshot. |
| `error` | IDE / OS / app error dialog or stack trace. |
| `code` | Editor or webpage code block screenshot. |
| `game` | Running game frame. |
| `webpage` | Browser screenshot. |
| `chat` | WeChat / Discord / iMessage screenshot. |
| `terminal` | Console / shell output. |
| `diagram` | Flowchart, architecture, wireframe, mindmap. |
| `comparison` | Split-screen before/after. |
| `table` | Spreadsheet or data table. |
| `lowquality` | Blurry / dark / compressed. |
| `ocr` | Pure text extraction. |

## How to write good `question` strings

The vision model is description-only. Phrase the question as **what to look at**, not **what to do**.

**Good** (focused observation):
- *"Transcribe the error stack verbatim, including file paths and line numbers."*
- *"List every button label in the toolbar from left to right."*
- *"What is the player's HP and energy? Is there an enemy on screen?"*

**Bad** (asks for reasoning the vision model is locked out of):
- ❌ *"Why is this failing?"* → the model will say "Not visible in image". Ask the user to circle the relevant area, or fetch the description first and reason on it yourself.
- ❌ *"How do I fix this UI bug?"* → same.
- ❌ *"Suggest improvements to the design."* → same.

After receiving the description, **you** (the reasoning model) do the diagnosis, fix-suggestion, or design critique.

## Path handling

- Use absolute paths. On Windows, forward slashes work fine: `C:/Users/foo/bar.png`.
- Do not pre-validate with stat/Read; just call `describe_image`. If the file is missing, the tool returns a clear error.

## Caching

Identical (image-bytes, model, full-prompt) tuples hit a local SHA-256-keyed cache. Don't hand-roll your own cache around this; the server already does it. Pass `bypass_cache: true` only when the underlying image has changed but the path is the same.

## What you should NOT do

- ❌ Re-call `describe_image` on the same image with the same question to "double-check". The first answer is what the vision model saw; if it said `Not visible in image`, that's the truth.
- ❌ Translate the verbatim transcription before reasoning on it. Stack traces and code must stay in their original form.
- ❌ Pass `question` strings that ask for solutions, opinions, or recommendations. The role lock will cause the vision model to refuse those parts and the response will degrade.
- ❌ Forward the raw description to the user as your final answer when the user asked a question that requires reasoning. Always synthesize.

## Configuring the server (for human users)

If `eyes` is not registered in the user's MCP client, point them at this repo's [README](README.md). All config is via environment variables; the only required ones are `MCP_EYES_PROTOCOL`, `MCP_EYES_BASE_URL`, `MCP_EYES_API_KEY`, `MCP_EYES_MODEL`.

After wiring the MCP server, the user must run `python -m mcp_eyes init --reasoning-model "<their-text-model>"` once per project to generate a `CLAUDE.md` / `AGENTS.md` snippet. The init step matters because **the server cannot detect which reasoning model is calling it** — that's whatever text LLM hosts the agent (GLM, DeepSeek, Claude, GPT-4, Kimi, etc.). Without the init snippet pasted into the project's agent docs, downstream agents won't know the eyes-only contract.

## Source map

```
src/mcp_eyes/
├── server.py            # MCP JSON-RPC dispatch + tool definitions
├── config.py            # env var → Config dataclass
├── image_utils.py       # load (file or URL), resize via Pillow, base64
├── prompts.py           # role lock + format rules + 14 scene templates (en + zh)
├── init_template.py     # `python -m mcp_eyes init` CLI for project bootstrap
└── providers/
    ├── base.py
    ├── openai_compat.py    # /v1/chat/completions
    └── anthropic_compat.py # /v1/messages
```

To add a new provider protocol, subclass `VisionProvider`, add it to `providers/__init__.py:make_provider`, and document the `MCP_EYES_PROTOCOL` value in the README.

To add a new scene, append to the `Scene` literal, add entries to `SCENES_EN` and `SCENES_ZH`, and update the keyword list in `detect_scene` if it should be auto-selectable.
