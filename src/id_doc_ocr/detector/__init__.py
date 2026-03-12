from id_doc_ocr.detector.base import DetectorAdapter, DetectorCapabilities, DetectorInfo
from id_doc_ocr.detector.contracts import DetectorResult, DocumentClassification, DocumentQuad
from id_doc_ocr.detector.mock import MockDocumentDetectorAdapter

__all__ = [
    "DetectorAdapter",
    "DetectorCapabilities",
    "DetectorInfo",
    "DetectorResult",
    "DocumentClassification",
    "DocumentQuad",
    "MockDocumentDetectorAdapter",
]
