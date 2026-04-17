from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

from id_doc_ocr.detector.base import DetectorAdapter, DetectorCapabilities, DetectorInfo
from id_doc_ocr.detector.contracts import DetectorResult, DocumentClassification, DocumentQuad
from id_doc_ocr.schemas.types import BoundingBox, DocumentDetection, Point
from id_doc_ocr.utils.runtime import module_available


class PillowDocumentDetectorAdapter(DetectorAdapter):
    info = DetectorInfo(
        name="pil_detector",
        description="Image-aware Pillow detector with lightweight document localization",
        version="0.1.0",
    )
    capabilities = DetectorCapabilities(
        document_localization=True,
        corner_detection=True,
        document_classification=False,
        supported_doc_types=[],
    )

    @classmethod
    def is_available(cls) -> bool:
        return module_available("PIL")

    @classmethod
    def availability_details(cls) -> dict[str, Any]:
        details = super().availability_details()
        details["package"] = "Pillow"
        if not details["available"]:
            details["reason"] = "module_spec_not_found"
        return details

    def detect(self, image: bytes | str | Path, *, preferred_doc_type: str | None = None) -> DetectorResult:
        normalized = self.normalize_image_input(image)
        source = normalized if isinstance(normalized, str) else f"bytes:{len(normalized)}"
        width, height = 1000, 640
        strategy = "fallback"

        try:
            pil_image = self._open_image(normalized)
            width, height = pil_image.size
            bbox = self._detect_bbox(pil_image)
            strategy = "pillow_bbox"
        except Exception:
            bbox = self._fallback_bbox(width, height)

        quad = self._quad_from_bbox(bbox)
        area_ratio = ((bbox.x2 - bbox.x1) * (bbox.y2 - bbox.y1)) / max(float(width * height), 1.0)
        confidence = round(min(0.98, max(0.55, 0.45 + (area_ratio * 0.6))), 3)
        doc_type = preferred_doc_type or "generic_document"
        primary = DocumentDetection(doc_type=doc_type, bbox=bbox, corners=list(quad.points), confidence=confidence)
        classifications = [DocumentClassification(label=doc_type, confidence=confidence)]
        if preferred_doc_type is None:
            classifications.append(DocumentClassification(label="unknown_document", confidence=max(0.35, confidence - 0.18)))
        return DetectorResult(
            primary=primary,
            quad=quad,
            classifications=classifications,
            model_version=self.info.version,
            raw={
                "adapter": self.info.name,
                "source": source,
                "preferred_doc_type": preferred_doc_type,
                "image_size": {"width": width, "height": height},
                "strategy": strategy,
            },
        )

    def _open_image(self, image: bytes | str):
        from PIL import Image

        if isinstance(image, bytes):
            return Image.open(BytesIO(image)).convert("RGB")
        return Image.open(image).convert("RGB")

    def _detect_bbox(self, image) -> BoundingBox:
        from PIL import Image, ImageChops

        gray = image.convert("L")
        width, height = gray.size
        corner_samples = [
            gray.getpixel((0, 0)),
            gray.getpixel((max(width - 1, 0), 0)),
            gray.getpixel((0, max(height - 1, 0))),
            gray.getpixel((max(width - 1, 0), max(height - 1, 0))),
        ]
        background = int(sum(corner_samples) / max(len(corner_samples), 1))
        diff = ImageChops.difference(gray, Image.new("L", gray.size, color=background))
        mask = diff.point(lambda value: 255 if value > 18 else 0)
        found = mask.getbbox()
        if found is None:
            return self._fallback_bbox(width, height)
        left, upper, right, lower = found
        if (right - left) < width * 0.2 or (lower - upper) < height * 0.2:
            return self._fallback_bbox(width, height)
        pad_x = max(2, int(width * 0.01))
        pad_y = max(2, int(height * 0.01))
        return BoundingBox(
            x1=max(0.0, float(left - pad_x)),
            y1=max(0.0, float(upper - pad_y)),
            x2=min(float(width), float(right + pad_x)),
            y2=min(float(height), float(lower + pad_y)),
        )

    def _fallback_bbox(self, width: int, height: int) -> BoundingBox:
        margin_x = max(24.0, width * 0.06)
        margin_y = max(24.0, height * 0.06)
        return BoundingBox(x1=margin_x, y1=margin_y, x2=max(margin_x + 1.0, width - margin_x), y2=max(margin_y + 1.0, height - margin_y))

    def _quad_from_bbox(self, bbox: BoundingBox) -> DocumentQuad:
        return DocumentQuad(
            points=[
                Point(x=bbox.x1, y=bbox.y1),
                Point(x=bbox.x2, y=bbox.y1),
                Point(x=bbox.x2, y=bbox.y2),
                Point(x=bbox.x1, y=bbox.y2),
            ]
        )