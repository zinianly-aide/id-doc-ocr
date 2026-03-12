from id_doc_ocr.core.contracts import PluginMetadata
from id_doc_ocr.plugins.base import BaseDocumentPlugin
from id_doc_ocr.plugins.china_id.parser import parse_china_id_fields
from id_doc_ocr.validator.china_id import build_china_id_validation_report


class ChinaIdPlugin(BaseDocumentPlugin):
    metadata = PluginMetadata(
        name='china_id',
        description='china_id document plugin',
        supported_backbones=['paddleocr', 'paddleocr_vl'],
        tags=['document-plugin'],
    )

    def get_schema_name(self) -> str:
        return 'china_id'

    def parse_fields(self, ocr_result: dict) -> dict:
        return parse_china_id_fields(ocr_result)

    def validate_fields(self, fields: dict) -> dict:
        return build_china_id_validation_report(fields.get("id_number")).model_dump()


plugin = ChinaIdPlugin()
