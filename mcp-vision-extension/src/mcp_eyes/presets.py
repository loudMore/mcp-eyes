"""Provider presets — the lookup table installing agents use to map a friendly
name (what the user types: 'doubao' / 'openai' / 'qwen') to a concrete
(protocol, base_url, default_model, key_format_hint) tuple.

When the user asks an agent to install mcp-eyes, the agent reads this list,
asks the user "which provider?", asks for the API key, and writes .mcp.json.
No protocol or URL trivia leaks into the conversation.

To add a new preset: append to PRESETS. Required keys: protocol, base_url,
default_model, key_format_hint, notes.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable


@dataclass(frozen=True)
class Preset:
    name: str
    aliases: tuple[str, ...]
    protocol: str
    base_url: str
    default_model: str
    available_models: tuple[str, ...]
    key_format_hint: str
    key_signup_url: str
    notes: str


PRESETS: tuple[Preset, ...] = (
    Preset(
        name="doubao",
        aliases=("volcano", "ark", "volcengine", "huoshan", "火山", "豆包"),
        protocol="openai",
        base_url="https://ark.cn-beijing.volces.com/api/coding/v3",
        default_model="doubao-seed-2.0-pro",
        available_models=("doubao-seed-2.0-pro", "doubao-seed-1.6-vision", "doubao-1.5-vision-pro-32k"),
        key_format_hint="ark-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        key_signup_url="https://www.volcengine.com/product/ark",
        notes="Volcano Engine Ark — China-region, fast, cheap. Coding plan endpoint includes vision models.",
    ),
    Preset(
        name="doubao-anthropic",
        aliases=("volcano-anthropic", "ark-anthropic"),
        protocol="anthropic",
        base_url="https://ark.cn-beijing.volces.com/api/coding",
        default_model="doubao-seed-1-6-vision",
        available_models=("doubao-seed-1-6-vision",),
        key_format_hint="ark-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        key_signup_url="https://www.volcengine.com/product/ark",
        notes="Volcano Engine via Anthropic-compatible protocol. Use this if your reasoning model already uses Anthropic protocol.",
    ),
    Preset(
        name="openai",
        aliases=("gpt-4o", "gpt", "chatgpt"),
        protocol="openai",
        base_url="https://api.openai.com/v1",
        default_model="gpt-4o-mini",
        available_models=("gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4.1", "gpt-4.1-mini"),
        key_format_hint="sk-...",
        key_signup_url="https://platform.openai.com/api-keys",
        notes="OpenAI native. gpt-4o-mini is cheapest; gpt-4o is highest quality.",
    ),
    Preset(
        name="anthropic",
        aliases=("claude",),
        protocol="anthropic",
        base_url="https://api.anthropic.com/v1",
        default_model="claude-sonnet-4-5",
        available_models=("claude-opus-4-7", "claude-sonnet-4-5", "claude-haiku-4-5"),
        key_format_hint="sk-ant-...",
        key_signup_url="https://console.anthropic.com/settings/keys",
        notes="Anthropic native. Sonnet 4.5 is the recommended balance of quality and cost.",
    ),
    Preset(
        name="qwen",
        aliases=("dashscope", "tongyi", "通义", "千问"),
        protocol="openai",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        default_model="qwen-vl-max",
        available_models=("qwen-vl-max", "qwen-vl-plus", "qwen2.5-vl-72b-instruct", "qwen2.5-vl-7b-instruct"),
        key_format_hint="sk-...",
        key_signup_url="https://dashscope.console.aliyun.com/apiKey",
        notes="Alibaba DashScope. qwen-vl-max is strongest; qwen2.5-vl-7b is cheapest.",
    ),
    Preset(
        name="zhipu",
        aliases=("glm", "glm-4v", "智谱"),
        protocol="openai",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        default_model="glm-4v-plus",
        available_models=("glm-4v-plus", "glm-4v", "glm-4v-flash"),
        key_format_hint="<id>.<secret>",
        key_signup_url="https://open.bigmodel.cn/usercenter/apikeys",
        notes="Zhipu (智谱) GLM. glm-4v-flash has a free tier.",
    ),
    Preset(
        name="gemini",
        aliases=("google", "google-ai"),
        protocol="openai",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        default_model="gemini-2.5-pro",
        available_models=("gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"),
        key_format_hint="AIza...",
        key_signup_url="https://aistudio.google.com/apikey",
        notes="Google Gemini via its OpenAI-compatible endpoint. flash variants are cheaper and faster.",
    ),
    Preset(
        name="siliconflow",
        aliases=("sf", "硅基流动"),
        protocol="openai",
        base_url="https://api.siliconflow.cn/v1",
        default_model="Qwen/Qwen2.5-VL-72B-Instruct",
        available_models=(
            "Qwen/Qwen2.5-VL-72B-Instruct",
            "Qwen/Qwen2.5-VL-7B-Instruct",
            "deepseek-ai/deepseek-vl2",
            "OpenGVLab/InternVL2-26B",
        ),
        key_format_hint="sk-...",
        key_signup_url="https://cloud.siliconflow.cn/account/ak",
        notes="SiliconFlow aggregator — multiple open-weight vision models on one endpoint.",
    ),
    Preset(
        name="openrouter",
        aliases=("or",),
        protocol="openai",
        base_url="https://openrouter.ai/api/v1",
        default_model="openai/gpt-4o-mini",
        available_models=(
            "openai/gpt-4o", "openai/gpt-4o-mini",
            "anthropic/claude-sonnet-4.5",
            "google/gemini-2.5-pro",
            "qwen/qwen2.5-vl-72b-instruct",
        ),
        key_format_hint="sk-or-...",
        key_signup_url="https://openrouter.ai/keys",
        notes="OpenRouter aggregator. Pick any vision model from their catalog by full slug.",
    ),
    Preset(
        name="ollama",
        aliases=("local",),
        protocol="openai",
        base_url="http://localhost:11434/v1",
        default_model="qwen2.5vl:7b",
        available_models=("qwen2.5vl:7b", "qwen2.5vl:32b", "llava:13b", "llava:34b", "minicpm-v:8b"),
        key_format_hint="(any non-empty string, Ollama ignores it; e.g. 'ollama')",
        key_signup_url="https://ollama.com/library?q=vision",
        notes="Local Ollama server. Free, private, no API key needed (pass any placeholder). Pull the model first: 'ollama pull qwen2.5vl:7b'.",
    ),
    Preset(
        name="moonshot",
        aliases=("kimi",),
        protocol="openai",
        base_url="https://api.moonshot.cn/v1",
        default_model="moonshot-v1-8k-vision-preview",
        available_models=("moonshot-v1-8k-vision-preview", "moonshot-v1-32k-vision-preview", "moonshot-v1-128k-vision-preview"),
        key_format_hint="sk-...",
        key_signup_url="https://platform.moonshot.cn/console/api-keys",
        notes="Moonshot (Kimi) vision. Long context variants available.",
    ),
    Preset(
        name="deepseek",
        aliases=(),
        protocol="openai",
        base_url="https://api.deepseek.com/v1",
        default_model="deepseek-vl2",
        available_models=("deepseek-vl2",),
        key_format_hint="sk-...",
        key_signup_url="https://platform.deepseek.com/api_keys",
        notes="DeepSeek vision (VL2). Note: as of 2026, DeepSeek's primary chat API may not yet expose vision — verify on their platform first.",
    ),
)


def find_preset(name_or_alias: str) -> Preset | None:
    needle = name_or_alias.strip().lower()
    for p in PRESETS:
        if p.name.lower() == needle:
            return p
        if needle in (a.lower() for a in p.aliases):
            return p
    return None


def all_presets_dict() -> list[dict]:
    return [asdict(p) for p in PRESETS]


def preset_names() -> list[str]:
    return [p.name for p in PRESETS]


def search_presets(query: str) -> Iterable[Preset]:
    q = query.strip().lower()
    for p in PRESETS:
        hay = " ".join([p.name, *p.aliases, p.notes]).lower()
        if q in hay:
            yield p
