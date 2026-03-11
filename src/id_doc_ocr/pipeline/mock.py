from id_doc_ocr.pipeline.base import IdentityDocumentPipeline
from id_doc_ocr.schemas.types import BoundingBox, DocumentDetection, StructuredDocument, ValidationReport
from id_doc_ocr.validator.china_id import build_china_id_validation_report


class MockChinaIdPipeline(IdentityDocumentPipeline):
    def detect(self, image: bytes) -> DocumentDetection:
        return DocumentDetection(
            doc_type="china_resident_id_front",
            bbox=BoundingBox(x1=0, y1=0, x2=100, y2=60),
            corners=[],
            confidence=0.99,
        )

    def extract(self, image: bytes) -> StructuredDocument:
        return StructuredDocument(
            doc_type="china_resident_id_front",
            country_code="CHN",
            fields={
                "name": "张三",
                "gender": "男",
                "birth_date": "1990-01-01",
                "id_number": "110101199001011234",
            },
            field_results=[],
        )

    def validate(self, document: StructuredDocument) -> ValidationReport:
        return build_china_id_validation_report(document.fields.get("id_number"))
