from id_doc_ocr.core.contracts import PluginMetadata
from id_doc_ocr.plugins.base import BaseDocumentPlugin
from id_doc_ocr.plugins.train_ticket.validator import validate_train_ticket


class TrainTicketPlugin(BaseDocumentPlugin):
    metadata = PluginMetadata(
        name='train_ticket',
        description='train_ticket document plugin',
        supported_backbones=['paddleocr', 'paddleocr_vl'],
        tags=['document-plugin'],
    )

    def get_schema_name(self) -> str:
        return 'train_ticket'

    def validate_fields(self, fields: dict) -> dict:
        return validate_train_ticket(fields).model_dump()


plugin = TrainTicketPlugin()
