from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BackboneInfo:
    name: str
    kind: str
    description: str = ""


class OCRBackboneAdapter:
    info: BackboneInfo

    def infer(self, image: bytes) -> dict:
        raise NotImplementedError
