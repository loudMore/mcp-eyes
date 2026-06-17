# vision-extension

> **Drop-in vision capability pack for text-only reasoning LLMs.**
> One repo containing an MCP server and a Claude Code skill, both engineered around a single contract: **the vision model only describes — your reasoning model does the thinking.**

[English](#english) · [中文](#中文)

---

## English

### What's in this repo

| Directory | What it is | Who installs it |
|---|---|---|
| [`mcp-vision-extension/`](mcp-vision-extension/) | The MCP server (Python package `mcp_eyes`). Pairs any text-only reasoning model with any vision model over OpenAI or Anthropic protocol. | Required. Install once per machine. |
| [`skills-vision-extension/`](skills-vision-extension/) | A Claude Code skill that knows the install playbook AND the day-to-day collaboration patterns between the reasoning model and the vision model. | Optional but strongly recommended for Claude Code users. Copy into `~/.claude/skills/`. |

These two pieces are designed to work together. The MCP server gives your text model eyes; the skill teaches your text model how to use those eyes well.

### Install everything in 2 commands

```bash
# 1. The MCP server
pip install "git+https://github.com/loudMore/vision-extension.git#subdirectory=mcp-vision-extension"

# 2. The Claude Code skill (optional)
git clone https://github.com/loudMore/vision-extension.git /tmp/vx
cp -r /tmp/vx/skills-vision-extension/vision-extension ~/.claude/skills/
```

Then point your MCP client at the new server. Detailed steps + provider presets in [`mcp-vision-extension/README.md`](mcp-vision-extension/README.md).

### Or just tell your agent

If you have Claude Code (or any MCP-aware agent), copy the skill once:

```bash
git clone https://github.com/loudMore/vision-extension.git
cp -r vision-extension/skills-vision-extension/vision-extension ~/.claude/skills/
```

Then say:

> *"Install vision-extension. Use the `<doubao | openai | qwen | gemini | ollama | …>` provider. Here's my key: `<KEY>`."*

The skill handles the rest. You don't write any JSON.

### Why this exists

Long-context reasoning models (GLM-4.6, DeepSeek-R1, Kimi K2, o1, …) are extraordinary at code and analysis but **cannot see images**. Naively bolting on a vision API has two problems:

1. **No standard pipe** — every IDE wires it differently.
2. **Vision models love to "help"** — GPT-4o, Gemini, Doubao all reflexively produce advice, debugging hypotheses, and design opinions when you only wanted a description. The reasoning work gets fragmented.

vision-extension solves both:

- **One MCP server**, works with Claude Code, Cursor, Continue, Cline, Roo, or anything else that speaks MCP.
- **Eyes-only contract** — the vision model is system-prompted into a pure visual scanner. No advice. No fixes. No opinions. Just verbatim transcription and structured description.
- **One Claude Code skill** that turns the install + daily-use rules into a single trigger phrase.
- **Provider-agnostic** — Anthropic protocol, OpenAI-compatible protocol. Switch with one env var.

### License

MIT.

---

## 中文

### 仓库里有什么

| 目录 | 是什么 | 谁要装 |
|---|---|---|
| [`mcp-vision-extension/`](mcp-vision-extension/) | MCP server（Python 包 `mcp_eyes`），把任意纯文本推理模型和任意视觉模型用 OpenAI/Anthropic 协议接到一起 | 必装，每台机器装一次 |
| [`skills-vision-extension/`](skills-vision-extension/) | Claude Code skill，把安装流程 + 主模型与视觉模型的日常协作规则打包好 | 强烈推荐，复制到 `~/.claude/skills/` 即可 |

两块组件协同设计。MCP server 给文本模型装上眼睛；skill 教文本模型怎么用好这双眼睛。

### 两条命令搞定

```bash
# 1. 装 MCP server
pip install "git+https://github.com/loudMore/vision-extension.git#subdirectory=mcp-vision-extension"

# 2. 装 Claude Code skill（可选）
git clone https://github.com/loudMore/vision-extension.git /tmp/vx
cp -r /tmp/vx/skills-vision-extension/vision-extension ~/.claude/skills/
```

然后让你的 MCP 客户端配新 server。详细步骤和 12 个 provider 预设见 [`mcp-vision-extension/README.md`](mcp-vision-extension/README.md)。

### 或者直接让你的 agent 装

装完 skill 之后，对你的 Claude Code（或任何支持 MCP 的 agent）说：

> *"装个 vision-extension。视觉模型用 `<豆包 | openai | 通义 | 智谱 | ollama | …>`，key 是 `<KEY>`。"*

skill 会按 7 步确定流程把剩下的全做完。你不用写任何 JSON。

### 为什么做这个

GLM-4.6 / DeepSeek-R1 / Kimi K2 / o1 这类长上下文推理模型推理超强，但**看不见图**。直接接个视觉 API 拼起来有两个老问题：

1. **没有统一通道** —— 每个 IDE 接法都不一样
2. **视觉模型爱"帮忙"** —— GPT-4o / Gemini / 豆包都会条件反射地给方案、提假设、写评价，把推理工作抢走一半，你只想要个描述

vision-extension 一并解决：

- **一个 MCP server**，Claude Code / Cursor / Continue / Cline / Roo 通用
- **eyes-only 契约** —— 视觉模型被系统提示锁成纯扫描器，不给建议、不给方案、不给评价，只做逐字转录和结构化描述
- **一个 Claude Code skill** 把安装流程和日常使用规则压成一句话触发
- **协议解耦** —— Anthropic 协议、OpenAI 协议都支持，一个环境变量切换

### License

MIT。
