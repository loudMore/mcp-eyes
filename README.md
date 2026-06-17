# mcp-eyes

> **Give text-only reasoning LLMs a pair of eyes.**
> A drop-in MCP server that pairs any long-context reasoning model (GLM, DeepSeek-R1, o1, Kimi, …) with any vision model — and crucially, locks the vision model into **description-only mode** so the reasoning model stays in charge of thinking.

[English](#english) · [中文](#中文)

---

## English

### Why this exists

Long-context reasoning models like GLM-4.6, DeepSeek-R1, Kimi, o1 are amazing at code & analysis but **cannot see images**. The naïve fix — call a vision API and dump its answer in — has two problems:

1. **No standard pipe.** Different IDEs, different protocols, different SDKs.
2. **Vision models love to "help".** GPT-4o, Gemini, and Doubao all reflexively give advice, debugging suggestions, and opinions. When you wanted a description, you got a co-author.

`mcp-eyes` solves both:

- **One MCP server**, works with Claude Code, Cursor, Continue, Cline, or anything else that speaks MCP.
- **Eyes-only protocol** — the vision model is system-prompted into a pure visual scanner. No advice. No fixes. No opinions. Just verbatim transcription and structured description. Reasoning stays with your reasoning model.
- **Provider-agnostic** — Anthropic protocol, OpenAI-compatible protocol. Switch with one env var.

### Compatible providers

| Provider | Protocol | Example model |
|---|---|---|
| Anthropic | `anthropic` | `claude-sonnet-4-5` |
| Volcano Ark (Anthropic) | `anthropic` | `doubao-seed-1-6-vision`, `claude-…` |
| Volcano Ark (OpenAI) | `openai` | `doubao-seed-2.0-pro`, `doubao-vision-…` |
| OpenAI | `openai` | `gpt-4o`, `gpt-4o-mini` |
| Google Gemini (OpenAI mode) | `openai` | `gemini-2.5-pro` |
| Zhipu | `openai` | `glm-4v-plus` |
| Qwen (DashScope) | `openai` | `qwen-vl-max` |
| SiliconFlow / OpenRouter | `openai` | any vision model on the platform |
| Ollama (local) | `openai` | `llava`, `qwen2-vl`, `minicpm-v` |

If your provider exposes `/v1/chat/completions` or Anthropic `/v1/messages`, it works.

### Install

```bash
pip install git+https://github.com/loudMore/mcp-eyes.git
```

Or with auto-resize for large images:

```bash
pip install "mcp-eyes[resize] @ git+https://github.com/loudMore/mcp-eyes.git"
```

### Quick setup (have your AI agent do it for you)

Tell your coding agent:

> *"Install mcp-eyes from `https://github.com/loudMore/mcp-eyes`. I want to use the `<doubao | openai | qwen | gemini | ollama | …>` provider. Here's my API key: `<KEY>`."*

That's it — you don't have to specify which reasoning model is running the agent (the agent knows itself). The agent follows [`AGENT_SETUP.md`](AGENT_SETUP.md): install the package, write `.mcp.json`, generate the `CLAUDE.md` snippet, run `doctor` to verify. You don't write any JSON.

### Manual setup (4 commands)

```bash
# 1. List supported providers
python -m mcp_eyes presets

# 2. Generate .mcp.json (writes a server entry)
python -m mcp_eyes config --preset doubao --api-key sk-... --merge --out .mcp.json

# 3. Generate the CLAUDE.md snippet that tells future agents in this project how to call mcp-eyes
python -m mcp_eyes init --lang zh --out CLAUDE.md.eyes-section

# 4. Self-check
python -m mcp_eyes doctor --image C:/path/to/test.png
```

### Configure

All config is via env vars. Three required, the rest optional with sane defaults.

| Variable | Required | Default | Description |
|---|---|---|---|
| `MCP_EYES_PROTOCOL` | ✓ | — | `openai` or `anthropic`. See [Choosing a protocol](#choosing-a-protocol). |
| `MCP_EYES_BASE_URL` | ✓ | — | API endpoint, no trailing slash, no `/chat/completions` or `/messages` suffix. |
| `MCP_EYES_API_KEY` | ✓ | — | Provider API key. |
| `MCP_EYES_MODEL` | ✓ | — | Vision model identifier (e.g. `doubao-seed-2.0-pro`, `gpt-4o-mini`). |
| `MCP_EYES_LANG` | | `auto` | `auto` / `en` / `zh`. `auto` detects from the question text. |
| `MCP_EYES_MAX_IMAGE_DIM` | | `2048` | Auto-resize longest edge to this many px (Pillow required). `0` disables. |
| `MCP_EYES_MAX_TOKENS` | | `1536` | Vision model `max_tokens`. |
| `MCP_EYES_TEMPERATURE` | | `0.2` | Sampling temperature. Lower = more deterministic transcription. |
| `MCP_EYES_TIMEOUT` | | `90` | HTTP timeout, seconds. |
| `MCP_EYES_CACHE_ENABLED` | | `true` | Disk cache for (image-hash + prompt + model). |
| `MCP_EYES_CACHE_DIR` | | `~/.cache/mcp-eyes` | Cache location. |
| `MCP_EYES_ANTHROPIC_VERSION` | | `2023-06-01` | Anthropic protocol only. The `anthropic-version` header value. |

You can also use `python -m mcp_eyes config` (see above) to generate `.mcp.json` so you never hand-write any of these.

### Choosing a protocol

mcp-eyes speaks two HTTP protocols. Pick whichever the provider you want to use exposes.

- **`openai`** — uses `/chat/completions` with `image_url` parts. **Use this for almost everything**: OpenAI, Volcano Ark `/api/coding/v3`, Gemini OpenAI mode, Qwen DashScope, Zhipu, SiliconFlow, OpenRouter, Moonshot, DeepSeek, Ollama, vLLM, LiteLLM proxies, OneAPI, etc. ~95% of vision endpoints in the wild.
- **`anthropic`** — uses `/messages` with `image` parts whose `source.type=base64`. Use this for Anthropic native, Volcano Ark `/api/coding`, AWS Bedrock proxies that speak Anthropic, or any gateway documented as "Anthropic-compatible".

If you're using a preset, the protocol is already set correctly. If you're configuring a custom endpoint and aren't sure: read the provider's "Quickstart" — if their example calls `/chat/completions`, pick `openai`; if it calls `/messages`, pick `anthropic`.

### Wire into Claude Code

Edit `~/.claude.json` (or use `claude mcp add`):

```json
{
  "mcpServers": {
    "eyes": {
      "command": "python",
      "args": ["-m", "mcp_eyes"],
      "env": {
        "MCP_EYES_PROTOCOL": "openai",
        "MCP_EYES_BASE_URL": "https://ark.cn-beijing.volces.com/api/coding/v3",
        "MCP_EYES_API_KEY": "sk-...",
        "MCP_EYES_MODEL": "doubao-seed-2.0-pro"
      }
    }
  }
}
```

See [`examples/`](examples/) for Cursor, Continue, Cline configs.

### One-time per-project init

After wiring the server, run **once** in each project to generate a CLAUDE.md / AGENTS.md snippet so future agents working in this project know mcp-eyes is available:

```bash
python -m mcp_eyes init --lang zh --out CLAUDE.md.eyes-section
```

The output reads the configured `MCP_EYES_*` env vars and produces a Markdown block you paste into your project's `CLAUDE.md`. The default snippet is **model-agnostic** — it doesn't matter which text reasoning model you happen to be running, the eyes-only contract works the same for all of them.

If you want the snippet to mention your specific model (cosmetic, optional), add `--reasoning-model "<your-name>"` — e.g. `glm-5.2`, `deepseek-v4-pro`, `claude-sonnet-4-5`, `gpt-4o`, `kimi-k2`. Skip it otherwise.

### Tools exposed

| Tool | Use case |
|---|---|
| `describe_image` | Single image → structured description. Pick a `scene` for tighter prompts. |
| `compare_images` | 2–6 images → comparative description (before/after, A/B, frames). |
| `extract_text` | Pure OCR shortcut. Equivalent to `describe_image` with `scene=ocr`. |

### Scene presets

`scene` selects the description template. `auto` infers from the question.

`auto`, `general`, `annotated`, `ui`, `error`, `code`, `game`, `webpage`, `chat`, `terminal`, `diagram`, `comparison`, `table`, `lowquality`, `ocr`

### The eyes-only protocol

Every prompt is assembled as **ROLE → FORMAT → SCENE → user question**. The role block explicitly bans:

- Solutions, fixes, debugging steps
- Phrases like *"you should"*, *"the cause is likely"*, *"try"*
- Evaluations or opinions
- Speculating about user intent
- Background knowledge not in the image
- Asking questions back

The result reads like a structured scanner log, which is exactly what a reasoning model wants as input. See `src/mcp_eyes/prompts.py` for the full text.

### Caching

Cache key = SHA-256(image bytes after resize) + model + full prompt. Same image + same question + same model = zero cost on the second call. Pass `bypass_cache: true` to force a fresh call.

### License

MIT.

### 配套 Claude Code skills

仓库 [`skills/`](skills/) 下两个 Claude Code skill：

- **`install-mcp-eyes`** —— 安装阶段触发，按 7 步确定流程让用户只出 API key 就能装好
- **`use-mcp-eyes`** —— 日常调用阶段触发，教主模型怎么跟视觉模型高效协作：选哪个 `scene`、`question` 怎么写才能被 eyes-only 协议接住、什么时候用 `compare_images`、什么时候**不该**调（描述已在上下文里）、答得不对怎么救

```bash
cp -r skills/install-mcp-eyes skills/use-mcp-eyes ~/.claude/skills/
```

装上之后从安装到日用都不需要你手动 babysit。详见 [`skills/README.md`](skills/README.md)。

---

### Companion Claude Code skills

This repo ships two [Claude Code skills](skills/) at `skills/`:

- **`install-mcp-eyes`** — fires on intent to install. Walks the agent through the deterministic 7-step install playbook so the user only provides their vision API key.
- **`use-mcp-eyes`** — fires whenever the agent is about to call mcp-eyes tools or the user sends an image path. Teaches the reasoning model how to talk to the eyes-only vision model effectively: which `scene` to pick, how to phrase `question` strings, when to batch images, when **not** to call vision (e.g. the description is already in conversation), and how to recover from "Not visible in image" responses.

```bash
cp -r skills/install-mcp-eyes skills/use-mcp-eyes ~/.claude/skills/
```

After that, the entire vision workflow — from install to daily use — is on rails. See [`skills/README.md`](skills/README.md).

### 为什么做这个

像 GLM-4.6 / DeepSeek-R1 / Kimi / o1 这样的长上下文推理模型推理超强，但**看不见图**。直接调视觉 API 拼起来有两个老问题：

1. **没有统一通道**。不同 IDE、不同协议、不同 SDK 各搞各的。
2. **视觉模型爱"帮忙"**。GPT-4o、Gemini、豆包都会条件反射给建议、提方案、写评价 —— 你只想要个描述，结果它把推理工作抢了一半。

`mcp-eyes` 一次解决两个：

- **一个 MCP 服务**，Claude Code / Cursor / Continue / Cline 通用。
- **eyes-only 协议** —— 视觉模型被系统提示锁成纯扫描器。不给建议、不给方案、不给评价，只做逐字转录和结构化描述。推理留给你的推理模型。
- **协议解耦** —— Anthropic 协议、OpenAI 协议都支持，一个环境变量切换。

### 支持的供应商

| 供应商 | 协议 | 示例模型 |
|---|---|---|
| Anthropic 官方 | `anthropic` | `claude-sonnet-4-5` |
| 火山引擎 Ark（Anthropic 兼容）| `anthropic` | `doubao-seed-1-6-vision`, `claude-…` |
| 火山引擎 Ark（OpenAI 兼容）| `openai` | `doubao-seed-2.0-pro` |
| OpenAI | `openai` | `gpt-4o`, `gpt-4o-mini` |
| Google Gemini（OpenAI 模式）| `openai` | `gemini-2.5-pro` |
| 智谱 | `openai` | `glm-4v-plus` |
| 通义千问（DashScope）| `openai` | `qwen-vl-max` |
| 硅基流动 / OpenRouter | `openai` | 平台上任意视觉模型 |
| Ollama（本地）| `openai` | `llava`, `qwen2-vl`, `minicpm-v` |

只要厂商开放 `/v1/chat/completions` 或 Anthropic 的 `/v1/messages`，就能用。

### 安装

```bash
pip install git+https://github.com/loudMore/mcp-eyes.git
```

带自动缩图：

```bash
pip install "mcp-eyes[resize] @ git+https://github.com/loudMore/mcp-eyes.git"
```

### 让你的 agent 帮你装好（推荐）

直接告诉你的 Coding Agent：

> *"用 https://github.com/loudMore/mcp-eyes 这个 MCP 给你装上眼睛。视觉模型用 `<豆包 | openai | 通义 | 智谱 | ollama | …>`，API key 是 `<KEY>`。"*

就这一句。**不用告诉它你的主模型是什么 —— agent 自己就是主模型，它知道自己是谁**。Agent 会按 [`AGENT_SETUP.md`](AGENT_SETUP.md) 自动：装包、写 `.mcp.json`、生成 `CLAUDE.md` 片段、跑 `doctor` 自检。你不用碰任何 JSON。

### 手动 4 条命令搞定

```bash
# 1. 看支持哪些 provider
python -m mcp_eyes presets

# 2. 写 .mcp.json（自动按预设填好 base_url/model）
python -m mcp_eyes config --preset doubao --api-key ark-... --merge --out .mcp.json

# 3. 生成 CLAUDE.md 片段（模型无关，不需要填主模型名）
python -m mcp_eyes init --lang zh --out CLAUDE.md.eyes-section

# 4. 自检
python -m mcp_eyes doctor --image C:/路径/test.png
```

### 配置

全部走环境变量。三个必填，其他可选并都有合理默认值。

| 变量 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `MCP_EYES_PROTOCOL` | ✓ | — | `openai` 或 `anthropic`，见下文 [选哪个协议](#选哪个协议) |
| `MCP_EYES_BASE_URL` | ✓ | — | API 端点，**不带**结尾斜杠，**不要**带 `/chat/completions` 或 `/messages` 后缀 |
| `MCP_EYES_API_KEY` | ✓ | — | 视觉模型的 API key |
| `MCP_EYES_MODEL` | ✓ | — | 视觉模型 ID（如 `doubao-seed-2.0-pro`、`gpt-4o-mini`）|
| `MCP_EYES_LANG` |  | `auto` | `auto` / `en` / `zh`，`auto` 按 question 文本自动判断 |
| `MCP_EYES_MAX_IMAGE_DIM` |  | `2048` | 自动把长边缩到这么多像素（需 Pillow），`0` 关闭 |
| `MCP_EYES_MAX_TOKENS` |  | `1536` | 视觉模型 `max_tokens` |
| `MCP_EYES_TEMPERATURE` |  | `0.2` | 采样温度，越低转录越稳 |
| `MCP_EYES_TIMEOUT` |  | `90` | HTTP 超时（秒）|
| `MCP_EYES_CACHE_ENABLED` |  | `true` | 本地磁盘缓存（图 hash + prompt + 模型）|
| `MCP_EYES_CACHE_DIR` |  | `~/.cache/mcp-eyes` | 缓存目录 |
| `MCP_EYES_ANTHROPIC_VERSION` |  | `2023-06-01` | 仅 anthropic 协议用，发到 `anthropic-version` header |

也可以直接用 `python -m mcp_eyes config`（见上面）让 CLI 自动生成 `.mcp.json`，不用自己填这些。

### 选哪个协议

mcp-eyes 走两种 HTTP 协议，选你的视觉服务支持的那一个。

- **`openai`** —— 走 `/chat/completions`，图片用 `image_url` 字段。**绝大多数情况都选这个**：OpenAI、火山 Ark `/api/coding/v3`、Gemini OpenAI 模式、通义 DashScope、智谱、硅基流动、OpenRouter、Moonshot/Kimi、DeepSeek、Ollama、vLLM、LiteLLM 代理、OneAPI 等等，覆盖野外 ~95% 的视觉端点。
- **`anthropic`** —— 走 `/messages`，图片用 `image` + `source.type=base64`。Anthropic 原生、火山 Ark `/api/coding`、AWS Bedrock 的 Anthropic 兼容代理、或者任何写明 "Anthropic-compatible" 的网关用这个。

用 preset 的话协议已经设好了。自己配端点不确定时：看厂商的 Quickstart，例子里调的是 `/chat/completions` 就选 `openai`，调的是 `/messages` 就选 `anthropic`。

### 接入 Claude Code

编辑 `~/.claude.json`：

```json
{
  "mcpServers": {
    "eyes": {
      "command": "python",
      "args": ["-m", "mcp_eyes"],
      "env": {
        "MCP_EYES_PROTOCOL": "openai",
        "MCP_EYES_BASE_URL": "https://ark.cn-beijing.volces.com/api/coding/v3",
        "MCP_EYES_API_KEY": "sk-...",
        "MCP_EYES_MODEL": "doubao-seed-2.0-pro"
      }
    }
  }
}
```

火山引擎的 Anthropic 协议端点写：

```json
"MCP_EYES_PROTOCOL": "anthropic",
"MCP_EYES_BASE_URL": "https://ark.cn-beijing.volces.com/api/coding"
```

### 每个项目跑一次的初始化

接好 server 之后，**在每个要用 mcp-eyes 的项目里跑一次**，自动生成 CLAUDE.md / AGENTS.md 片段告诉项目里跑的 agent "这里有视觉能力可用"：

```bash
python -m mcp_eyes init --lang zh --out CLAUDE.md.eyes-section
```

输出会读 `MCP_EYES_*` 环境变量自动填好视觉模型/协议/base URL，然后生成一段 Markdown 粘进你项目的 `CLAUDE.md`。**默认是模型无关的** —— eyes-only 协议对所有文本推理模型一视同仁，不需要告诉它你的主模型是谁。

需要让片段里点名你的主模型（纯装饰，不影响功能）就加 `--reasoning-model "<名字>"`，比如 `glm-5.2` / `deepseek-v4-pro` / `claude-sonnet-4-5` / `gpt-4o` / `kimi-k2`。不需要就别加。

### 暴露的工具

| 工具 | 场景 |
|---|---|
| `describe_image` | 单图 → 结构化描述，可选 `scene` 锁定模板 |
| `compare_images` | 2–6 张图 → 对比描述（before/after、AB、帧序列）|
| `extract_text` | 纯 OCR，等价于 `scene=ocr` |

### 场景模板

`auto / general / annotated / ui / error / code / game / webpage / chat / terminal / diagram / comparison / table / lowquality / ocr`

`auto` 时会按问题关键词自动选模板。

### eyes-only 协议

每次调用拼接顺序：**角色锁死 → 格式规范 → 场景模板 → 用户问题**。角色块明令禁止：

- 给方案、修复建议、调试步骤
- "建议你..."、"原因可能是..."、"可以试试..." 这类句式
- 评价或意见
- 推测用户意图
- 图中没有的背景知识
- 反问用户

输出会像扫描仪日志：精简、客观、详尽。完整提示词见 `src/mcp_eyes/prompts.py`。

### 缓存

缓存键 = SHA-256(缩放后图片) + 模型名 + 完整提示词。同图 + 同问 + 同模型 = 第二次零成本。传 `bypass_cache: true` 可强制重新调用。

### 许可证

MIT。
