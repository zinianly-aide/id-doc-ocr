from id_doc_ocr.core.contracts import PluginMetadata
from id_doc_ocr.plugins.base import BaseDocumentPlugin
from id_doc_ocr.plugins.passport.parser import parse_passport_fields
from id_doc_ocr.plugins.passport.validator import validate_passport


class PassportPlugin(BaseDocumentPlugin):
    metadata = PluginMetadata(
        name='passport',
        description='passport document plugin',
        supported_backbones=['paddleocr', 'paddleocr_vl'],
        tags=['document-plugin'],
    )

    def get_schema_name(self) -> str:
        return 'passport'

    def parse_fields(self, ocr_result: dict) -> dict:
        return parse_passport_fields(ocr_result)

    def validate_fields(self, fields: dict) -> dict:
        return validate_passport(fields).model_dump()


plugin = PassportPlugin()
