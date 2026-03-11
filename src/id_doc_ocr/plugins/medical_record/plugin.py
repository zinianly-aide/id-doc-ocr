from id_doc_ocr.core.contracts import PluginMetadata
from id_doc_ocr.plugins.base import BaseDocumentPlugin
from id_doc_ocr.plugins.medical_record.parser import parse_medical_record_fields
from id_doc_ocr.plugins.medical_record.validator import validate_medical_record


class MedicalRecordPlugin(BaseDocumentPlugin):
    metadata = PluginMetadata(
        name='medical_record',
        description='medical_record document plugin',
        supported_backbones=['paddleocr', 'paddleocr_vl'],
        tags=['document-plugin'],
    )

    def get_schema_name(self) -> str:
        return 'medical_record'

    def parse_fields(self, ocr_result: dict) -> dict:
        return parse_medical_record_fields(ocr_result)

    def validate_fields(self, fields: dict) -> dict:
        return validate_medical_record(fields).model_dump()


plugin = MedicalRecordPlugin()
