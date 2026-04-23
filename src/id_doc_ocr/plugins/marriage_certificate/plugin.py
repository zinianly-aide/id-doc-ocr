from id_doc_ocr.core.contracts import PluginMetadata
from id_doc_ocr.plugins.base import BaseDocumentPlugin
from id_doc_ocr.plugins.marriage_certificate.parser import parse_marriage_certificate_fields
from id_doc_ocr.plugins.marriage_certificate.validator import validate_marriage_certificate


class MarriageCertificatePlugin(BaseDocumentPlugin):
    metadata = PluginMetadata(
        name="marriage_certificate",
        description="marriage certificate document plugin",
        supported_backbones=["paddleocr", "paddleocr_vl"],
        tags=["document-plugin", "civil-affairs", "china"],
    )

    def get_schema_name(self) -> str:
        return "marriage_certificate"

    def parse_fields(self, ocr_result: dict) -> dict:
        return parse_marriage_certificate_fields(ocr_result)

    def validate_fields(self, fields: dict) -> dict:
        return validate_marriage_certificate(fields).model_dump()


plugin = MarriageCertificatePlugin()
