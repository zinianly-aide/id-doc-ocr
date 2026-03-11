from id_doc_ocr.core.contracts import PluginMetadata
from id_doc_ocr.plugins.base import BaseDocumentPlugin


class PassportPlugin(BaseDocumentPlugin):
    metadata = PluginMetadata(
        name='passport',
        description='passport document plugin',
        supported_backbones=['paddleocr', 'paddleocr_vl'],
        tags=['document-plugin'],
    )

    def get_schema_name(self) -> str:
        return 'passport'


plugin = PassportPlugin()
