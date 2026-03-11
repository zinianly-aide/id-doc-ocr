from __future__ import annotations

from id_doc_ocr.core.contracts import PluginMetadata


class BaseDocumentPlugin:
    metadata: PluginMetadata

    def get_schema_name(self) -> str:
        raise NotImplementedError

    def get_default_config(self) -> dict:
        return {}

    def validate_fields(self, fields: dict) -> dict:
        return {"accepted": True, "issues": []}
