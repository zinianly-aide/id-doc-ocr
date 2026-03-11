from id_doc_ocr.core.contracts import PluginMetadata
from id_doc_ocr.plugins.base import BaseDocumentPlugin


class TrainTicketPlugin(BaseDocumentPlugin):
    metadata = PluginMetadata(
        name='train_ticket',
        description='train_ticket document plugin',
        supported_backbones=['paddleocr', 'paddleocr_vl'],
        tags=['document-plugin'],
    )

    def get_schema_name(self) -> str:
        return 'train_ticket'


plugin = TrainTicketPlugin()
