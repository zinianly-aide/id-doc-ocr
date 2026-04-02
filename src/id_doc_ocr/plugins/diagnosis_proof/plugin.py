from id_doc_ocr.core.contracts import PluginMetadata
from id_doc_ocr.plugins.base import BaseDocumentPlugin
from id_doc_ocr.plugins.diagnosis_proof.parser import parse_diagnosis_proof_fields
from id_doc_ocr.plugins.diagnosis_proof.validator import validate_diagnosis_proof


class DiagnosisProofPlugin(BaseDocumentPlugin):
    metadata = PluginMetadata(
        name="diagnosis_proof",
        description="diagnosis proof / diagnostic certificate plugin",
        supported_backbones=["paddleocr", "paddleocr_vl"],
        tags=["document-plugin", "medical"],
    )

    def get_schema_name(self) -> str:
        return "diagnosis_proof"

    def parse_fields(self, ocr_result: dict) -> dict:
        return parse_diagnosis_proof_fields(ocr_result)

    def validate_fields(self, fields: dict) -> dict:
        return validate_diagnosis_proof(fields).model_dump()


plugin = DiagnosisProofPlugin()
