from mcp_eyes.config import Config
from mcp_eyes.providers.base import VisionProvider
from mcp_eyes.providers.anthropic_compat import AnthropicProvider
from mcp_eyes.providers.openai_compat import OpenAIProvider


def make_provider(cfg: Config) -> VisionProvider:
    if cfg.protocol == "anthropic":
        return AnthropicProvider(cfg)
    return OpenAIProvider(cfg)


__all__ = ["VisionProvider", "make_provider"]
