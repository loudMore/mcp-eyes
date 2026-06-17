from vision_extension.config import Config
from vision_extension.providers.base import VisionProvider
from vision_extension.providers.anthropic_compat import AnthropicProvider
from vision_extension.providers.openai_compat import OpenAIProvider


def make_provider(cfg: Config) -> VisionProvider:
    if cfg.protocol == "anthropic":
        return AnthropicProvider(cfg)
    return OpenAIProvider(cfg)


__all__ = ["VisionProvider", "make_provider"]
