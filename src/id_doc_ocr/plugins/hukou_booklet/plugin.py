from id_doc_ocr.core.contracts import PluginMetadata
from id_doc_ocr.plugins.base import BaseDocumentPlugin
from id_doc_ocr.plugins.hukou_booklet.validator import validate_hukou_booklet


class HukouBookletPlugin(BaseDocumentPlugin):
    metadata = PluginMetadata(
        name='hukou_booklet',
        description='hukou_booklet document plugin',
        supported_backbones=['paddleocr', 'paddleocr_vl'],
        tags=['document-plugin'],
    )

    def get_schema_name(self) -> str:
        return 'hukou_booklet'

    def validate_fields(self, fields: dict) -> dict:
        return validate_hukou_booklet(fields).model_dump()


plugin = HukouBookletPlugin()
