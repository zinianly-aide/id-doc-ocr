from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from id_doc_ocr.detector.contracts import DetectorResult


@dataclass
class DetectorInfo:
    name: str
    kind: str = "detector"
    description: str = ""
    version: str = "0.1.0"


@dataclass
class DetectorCapabilities:
    document_localization: bool = True
    corner_detection: bool = True
    document_classification: bool = True
    supported_doc_types: list[str] = field(default_factory=list)


class DetectorAdapter:
    info: DetectorInfo
    capabilities = DetectorCapabilities()

    @classmethod
    def is_available(cls) -> bool:
        return True

    @classmethod
    def availability_details(cls) -> dict[str, Any]:
        return {
            "available": cls.is_available(),
            "name": cls.info.name,
            "kind": cls.info.kind,
        }

    @staticmethod
    def normalize_image_input(image: bytes | str | Path) -> bytes | str:
        if isinstance(image, Path):
            return str(image)
        return image

    def detect(self, image: bytes | str | Path, *, preferred_doc_type: str | None = None) -> DetectorResult:
        raise NotImplementedError
