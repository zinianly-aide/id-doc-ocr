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

    @staticmethod
    def normalize_text(value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @staticmethod
    def normalize_score(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def average_confidence(lines: list[dict[str, Any]], score_key: str = "score") -> float:
        if not lines:
            return 0.0
        scores = [OCRBackboneAdapter.normalize_score(item.get(score_key), 0.0) for item in lines]
        return sum(scores) / len(scores) if scores else 0.0

    def infer(self, image: bytes | str | Path) -> dict[str, Any]:
        raise NotImplementedError
