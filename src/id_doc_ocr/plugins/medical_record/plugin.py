from id_doc_ocr.core.contracts import PluginMetadata
from id_doc_ocr.plugins.base import BaseDocumentPlugin


class MedicalRecordPlugin(BaseDocumentPlugin):
    metadata = PluginMetadata(
        name='medical_record',
        description='medical_record document plugin',
        supported_backbones=['paddleocr', 'paddleocr_vl'],
        tags=['document-plugin'],
    )

    def get_schema_name(self) -> str:
        return 'medical_record'


plugin = MedicalRecordPlugin()
