from __future__ import annotations

from pathlib import Path

from id_doc_ocr.detector.base import DetectorAdapter, DetectorCapabilities, DetectorInfo
from id_doc_ocr.detector.contracts import DetectorResult, DocumentClassification, DocumentQuad
from id_doc_ocr.schemas.types import BoundingBox, DocumentDetection, Point


class MockDocumentDetectorAdapter(DetectorAdapter):
    info = DetectorInfo(
        name="mock_detector",
        description="Placeholder detector adapter with production-oriented result shape",
        version="0.1.0",
    )
    capabilities = DetectorCapabilities(
        document_localization=True,
        corner_detection=True,
        document_classification=True,
        supported_doc_types=[],
    )

    def detect(self, image: bytes | str | Path, *, preferred_doc_type: str | None = None) -> DetectorResult:
        normalized = self.normalize_image_input(image)
        pseudo_width = 1000.0
        pseudo_height = 640.0
        margin = 64.0
        bbox = BoundingBox(x1=margin, y1=margin, x2=pseudo_width - margin, y2=pseudo_height - margin)
        quad = DocumentQuad(
            points=[
                Point(x=bbox.x1, y=bbox.y1),
                Point(x=bbox.x2, y=bbox.y1),
                Point(x=bbox.x2, y=bbox.y2),
                Point(x=bbox.x1, y=bbox.y2),
            ]
        )
        doc_type = preferred_doc_type or "unknown_document"
        confidence = 0.96 if preferred_doc_type else 0.72
        primary = DocumentDetection(doc_type=doc_type, bbox=bbox, corners=list(quad.points), confidence=confidence)
        classifications = [DocumentClassification(label=doc_type, confidence=confidence)]
        if preferred_doc_type is None:
            classifications.append(DocumentClassification(label="generic_document", confidence=0.61))
        raw_source = normalized if isinstance(normalized, str) else f"bytes:{len(normalized)}"
        return DetectorResult(
            primary=primary,
            quad=quad,
            classifications=classifications,
            model_version=self.info.version,
            raw={
                "adapter": self.info.name,
                "source": raw_source,
                "preferred_doc_type": preferred_doc_type,
            },
        )
