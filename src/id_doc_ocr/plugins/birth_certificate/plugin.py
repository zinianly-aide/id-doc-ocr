from id_doc_ocr.core.contracts import PluginMetadata
from id_doc_ocr.plugins.base import BaseDocumentPlugin
from id_doc_ocr.plugins.birth_certificate.parser import parse_birth_certificate_fields
from id_doc_ocr.plugins.birth_certificate.validator import validate_birth_certificate


class BirthCertificatePlugin(BaseDocumentPlugin):
    metadata = PluginMetadata(
        name="birth_certificate",
        description="birth_certificate document plugin",
        supported_backbones=["paddleocr", "paddleocr_vl"],
        tags=["document-plugin", "medical", "china"],
    )

    def get_schema_name(self) -> str:
        return "birth_certificate"

    def parse_fields(self, ocr_result: dict) -> dict:
        return parse_birth_certificate_fields(ocr_result)

    def validate_fields(self, fields: dict) -> dict:
        return validate_birth_certificate(fields).model_dump()


plugin = BirthCertificatePlugin()
