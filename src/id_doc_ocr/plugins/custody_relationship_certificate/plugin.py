from id_doc_ocr.core.contracts import PluginMetadata
from id_doc_ocr.plugins.base import BaseDocumentPlugin
from id_doc_ocr.plugins.custody_relationship_certificate.parser import parse_custody_relationship_certificate_fields
from id_doc_ocr.plugins.custody_relationship_certificate.validator import validate_custody_relationship_certificate


class CustodyRelationshipCertificatePlugin(BaseDocumentPlugin):
    metadata = PluginMetadata(
        name="custody_relationship_certificate",
        description="custody_relationship_certificate document plugin",
        supported_backbones=["paddleocr", "paddleocr_vl"],
        tags=["document-plugin", "civil-affairs", "guardianship", "china"],
    )

    def get_schema_name(self) -> str:
        return "custody_relationship_certificate"

    def parse_fields(self, ocr_result: dict) -> dict:
        return parse_custody_relationship_certificate_fields(ocr_result)

    def validate_fields(self, fields: dict) -> dict:
        return validate_custody_relationship_certificate(fields).model_dump()


plugin = CustodyRelationshipCertificatePlugin()
