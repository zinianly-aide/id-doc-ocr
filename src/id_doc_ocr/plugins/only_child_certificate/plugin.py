from id_doc_ocr.core.contracts import PluginMetadata
from id_doc_ocr.plugins.base import BaseDocumentPlugin
from id_doc_ocr.plugins.only_child_certificate.parser import parse_only_child_certificate_fields
from id_doc_ocr.plugins.only_child_certificate.validator import validate_only_child_certificate


class OnlyChildCertificatePlugin(BaseDocumentPlugin):
    metadata = PluginMetadata(
        name="only_child_certificate",
        description="only_child_certificate document plugin",
        supported_backbones=["paddleocr", "paddleocr_vl"],
        tags=["document-plugin", "civil-affairs", "family-planning", "china"],
    )

    def get_schema_name(self) -> str:
        return "only_child_certificate"

    def parse_fields(self, ocr_result: dict) -> dict:
        return parse_only_child_certificate_fields(ocr_result)

    def validate_fields(self, fields: dict) -> dict:
        return validate_only_child_certificate(fields).model_dump()


plugin = OnlyChildCertificatePlugin()
