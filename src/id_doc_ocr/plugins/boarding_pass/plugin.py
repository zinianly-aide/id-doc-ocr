from id_doc_ocr.core.contracts import PluginMetadata
from id_doc_ocr.plugins.base import BaseDocumentPlugin
from id_doc_ocr.plugins.boarding_pass.parser import parse_boarding_pass_fields
from id_doc_ocr.plugins.boarding_pass.validator import validate_boarding_pass


class BoardingPassPlugin(BaseDocumentPlugin):
    metadata = PluginMetadata(
        name='boarding_pass',
        description='boarding pass document plugin',
        supported_backbones=['rapidocr', 'paddleocr', 'paddleocr_vl'],
        tags=['document-plugin'],
    )

    def get_schema_name(self) -> str:
        return 'boarding_pass'

    def parse_fields(self, ocr_result: dict) -> dict:
        return parse_boarding_pass_fields(ocr_result)

    def validate_fields(self, fields: dict) -> dict:
        return validate_boarding_pass(fields).model_dump()


plugin = BoardingPassPlugin()
