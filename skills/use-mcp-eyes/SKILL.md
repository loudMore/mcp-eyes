---
name: use-mcp-eyes
description: Use this skill whenever you are about to call any mcp-eyes tool (`mcp__eyes__describe_image`, `mcp__eyes__compare_images`, `mcp__eyes__extract_text`), the user gives you a local image path or http(s) image URL, or you are reasoning about a screenshot / UI / error dialog / diagram / chart / game frame / annotated picture. Provides decision rules for picking the right tool and `scene`, patterns for writing `question` strings the eyes-only vision model can actually answer, multi-image and multi-step workflows, error recovery when the description is wrong or empty, and rules for when to skip mcp-eyes entirely to save cost. Ensures the reasoning model and the vision model collaborate efficiently.
---

# use-mcp-eyes — collaboration playbook for image-heavy tasks

You (the reasoning model) have access to mcp-eyes tools. The vision model behind them is **locked into description-only mode** server-side: it will not give advice, opinions, hypotheses, or follow-up questions. All thinking, diagnosis, and synthesis is **your** job. This skill teaches you how to extract maximum signal per call.

## Quick decision tree

```
Image input arrives:
├─ Is it a single image path/URL?
│  ├─ Yes → mcp__eyes__describe_image
│  └─ Multiple, asking to compare → mcp__eyes__compare_images
│
├─ Need ONLY raw text from image (OCR)?
│  └─ mcp__eyes__extract_text  (cheaper / scene=ocr)
│
├─ Same image already described earlier in this conversation?
│  └─ DO NOT recall — reuse the prior description, you've already paid for it
│
└─ User describing an image in words (not sending one)?
   └─ DO NOT call mcp-eyes — there's no image to look at
```

## Picking `scene`

`scene="auto"` is fine when the question text contains obvious keywords. Override explicitly when you can — it sharpens the response materially.

| Situation | scene |
|---|---|
| User added red circles, arrows, highlights, or notes | `annotated` |
| Software UI / form / dashboard | `ui` |
| Error dialog, IDE/console exception, traceback | `error` |
| Editor / GitHub / web code block screenshot | `code` |
| Running game frame (HP bars, enemies, particles) | `game` |
| Browser page (article, doc, SO answer) | `webpage` |
| WeChat/Discord/Slack/iMessage screenshot | `chat` |
| Terminal / shell output | `terminal` |
| Flowchart, architecture, wireframe, mindmap | `diagram` |
| Side-by-side or before/after | `comparison` |
| Spreadsheet / data table | `table` |
| Blurry, dark, or compressed image | `lowquality` |
| Pure text extraction, no analysis | `ocr` |
| Nothing fits | `general` |

For multi-image calls (`compare_images`), default scene is `comparison` but you can override (e.g. compare two error screenshots → `error`).

## Writing `question` strings — patterns that work

The vision model answers **what** and **where**, not **why** and **how**. Use these patterns.

### Verbatim transcription (highest precision)

> "Transcribe the error stack VERBATIM, including file paths, line numbers, and any 'Caused by' chains. Preserve line breaks."

> "Transcribe every visible character in this code, preserving indentation (note tabs vs spaces). Include line numbers if visible."

> "List every menu item and button label in the toolbar from left to right, exactly as written."

### Targeted observation (region or element)

> "What does the element circled in red show? Transcribe any text on or near it."

> "Read the value next to the 'HP' label in the top-left HUD."

> "What is the URL in the address bar?"

### Structured enumeration (when you need a complete inventory)

> "List every node in the scene tree on the left panel, with its type icon, in order, indented by hierarchy level."

> "Enumerate every form field: label, current value, validation state."

### Specific yes/no observation

> "Is there a red error indicator anywhere on the screen? If yes, where, and what text is next to it?"

### Bad question patterns (will fail or waste tokens)

| ❌ Anti-pattern | ✅ Replace with |
|---|---|
| "Why is this error happening?" | "Transcribe the error verbatim." (then YOU diagnose) |
| "How do I fix this UI bug?" | "Describe the visual anomaly precisely (position, color, surrounding elements)." |
| "Is this design good?" | "List every UI element with its position and color." |
| "Suggest improvements" | (don't ask — vision model isn't allowed to opine) |
| "What should I do next?" | (don't ask — that's your job) |

If you accidentally ask the vision model a "why" question, it will say "Not visible in image" for that part. That's the role lock working as intended — re-ask as a "what" question.

## Multi-step workflows

Complex tasks usually need **one vision call to gather, then your own reasoning to act**. Don't make the vision model your entire pipeline.

### Debugging from a screenshot
1. `describe_image` with `scene=error` → get verbatim stack + visible context
2. *(your job)* Match the stack against codebase (Grep) → locate root cause
3. *(your job)* Propose a fix
4. **Do not** call vision again to "validate" the fix — fix the code, run the code

### UI redesign / regression
1. `describe_image` with `scene=ui` → get exhaustive layout map
2. *(your job)* Compare against intended design (in code or spec)
3. *(your job)* Identify diffs, propose changes
4. After implementing: optionally `compare_images` with before/after screenshots

### Game balancing from a frame
1. `describe_image` with `scene=game` → get HP/energy/score/wave numbers verbatim
2. *(your job)* Plug into damage formulas / progression curves
3. *(your job)* Recommend tuning

### Reading code from a screenshot before editing
1. `extract_text` (OCR) is enough — `scene=code` if you also need highlight info
2. Reconstruct the code as a string in your context
3. Find the file in the project, edit it directly — don't re-screenshot to verify

## Multi-image strategy

- **2–6 images, same scene**: one `compare_images` call. Order matters — pass them in the order you want compared.
- **7+ images**: batch into chunks of 6. Synthesize across batches yourself.
- **Animation / sequence frames**: name them `frame_01.png`, `frame_02.png` … so the vision model can refer to them by index in its response.
- **Same image, multiple questions**: just ask one well-crafted compound question. Each call is a separate API charge even if the image is cached locally.

## Cost / latency awareness

| Action | Effect |
|---|---|
| Same `image + question + scene + model` | **Cache hit, 0 cost** (server-side SHA256 cache) |
| Same image, **different** question | New API call, full cost |
| Compare 4 images in one call | One charge (with bigger payload), much faster than 4 calls |
| Image >5 MB without Pillow installed | Slow upload, possibly truncated — suggest user crops |
| Calling vision twice to "double-check" | Wasted money. The first answer is what the model saw. |

If you need to retry, pass `bypass_cache: true` only when the underlying file actually changed.

## Error recovery

| Vision returned... | Do this |
|---|---|
| "Not visible in image" for a specific question | Re-ask as a "what is at location X" question, or ask the user to circle the element |
| Description shorter than expected | Pick a more specific `scene`; ask for a structured enumeration |
| Garbled / mixed-language transcription | The image may be too small — ask user for a higher-resolution screenshot |
| Tool returns `vision call failed: 401` | API key wrong; tell user to re-run `mcp-eyes config` |
| Tool returns `vision call failed: 404` | Model name wrong; check `mcp-eyes presets` and pass `--model` |
| Tool returns `Image not found` | Path is wrong — confirm with user, use absolute forward-slash paths on Windows |

## When NOT to call mcp-eyes

- The user is **describing** an image in words (not sending one). They've already done the visual work; reason from their description.
- The image is already described **earlier in this conversation**. Reuse — don't pay twice.
- The user pasted **text that came from an image** (e.g. they OCR'd themselves and gave you the transcript). Work with the text.
- The image is a **logo / brand mark** the user obviously knows. They want help with something else; don't waste a call describing the logo.
- The task is **purely about code/text the user already typed in chat**, even if a screenshot is also pasted. The chat text is canonical.

## Output handling

The vision model returns a **structured description**, not a final answer. Your responsibilities after the call:

1. **Synthesize** — combine the description with codebase reads, prior context, and the user's actual question.
2. **Don't echo** — never paste the raw vision output back to the user as your reply unless they explicitly asked for a transcript. Summarize and act on it.
3. **Don't translate verbatim transcriptions** — stack traces, code, error codes must stay in their original language for further work.
4. **Cite spatial references** — when explaining your reasoning, reference positions the vision model gave ("the red-circled button at top-right"), not pixel coordinates.

## One-line summary

> The vision model is your eyes, not your brain. Use it to **see**, then **think** yourself. Ask it *what is there*, never *what to do*. Pick the right `scene`, write a precise `question`, and reuse cached descriptions instead of re-asking.
