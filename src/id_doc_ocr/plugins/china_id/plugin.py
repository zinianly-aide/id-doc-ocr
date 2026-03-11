from id_doc_ocr.core.contracts import PluginMetadata
from id_doc_ocr.plugins.base import BaseDocumentPlugin


class ChinaIdPlugin(BaseDocumentPlugin):
    metadata = PluginMetadata(
        name='china_id',
        description='china_id document plugin',
        supported_backbones=['paddleocr', 'paddleocr_vl'],
        tags=['document-plugin'],
    )

    def get_schema_name(self) -> str:
        return 'china_id'


plugin = ChinaIdPlugin()
