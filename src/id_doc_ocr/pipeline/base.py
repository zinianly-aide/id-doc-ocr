from id_doc_ocr.schemas.types import DocumentDetection, StructuredDocument, ValidationReport


class IdentityDocumentPipeline:
    def detect(self, image: bytes) -> DocumentDetection:
        raise NotImplementedError

    def extract(self, image: bytes) -> StructuredDocument:
        raise NotImplementedError

    def validate(self, document: StructuredDocument) -> ValidationReport:
        raise NotImplementedError
