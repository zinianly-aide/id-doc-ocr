from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class BackboneInfo:
    name: str
    kind: str
    description: str = ""


class OCRBackboneAdapter:
    info: BackboneInfo

    @classmethod
    def is_available(cls) -> bool:
        return True

    @classmethod
    def availability_details(cls) -> dict[str, Any]:
        return {"available": cls.is_available()}

    @staticmethod
    def normalize_image_input(image: bytes | str | Path) -> bytes | str:
        if isinstance(image, Path):
            return str(image)
        return image

    def infer(self, image: bytes | str | Path) -> dict[str, Any]:
        raise NotImplementedError
