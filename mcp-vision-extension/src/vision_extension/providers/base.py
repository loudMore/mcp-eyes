from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from vision_extension.config import Config


@dataclass(frozen=True)
class ImagePart:
    data: bytes
    mime: str


class VisionProvider(ABC):
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg

    @abstractmethod
    def describe(self, images: list[ImagePart], prompt: str) -> str:
        """Send the image(s) plus prompt to the vision model and return text."""
