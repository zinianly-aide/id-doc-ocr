from id_doc_ocr.core.contracts import PluginMetadata
from id_doc_ocr.plugins.base import BaseDocumentPlugin


class HukouBookletPlugin(BaseDocumentPlugin):
    metadata = PluginMetadata(
        name='hukou_booklet',
        description='hukou_booklet document plugin',
        supported_backbones=['paddleocr', 'paddleocr_vl'],
        tags=['document-plugin'],
    )

    def get_schema_name(self) -> str:
        return 'hukou_booklet'


plugin = HukouBookletPlugin()
