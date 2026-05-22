from __future__ import annotations

from id_doc_ocr.leave_audit.domain.models import LeaveAuditTask

LEAVE_TYPE_PLUGIN_MAPPING = {
    "MARRIAGE": "marriage_certificate",
    "SICK": "diagnosis_proof",
    "MATERNITY": "birth_certificate",
    "PATERNITY": "birth_certificate",
    "PARENTAL": "birth_certificate",
    "BEREAVEMENT": "custody_relationship_certificate",
}


def resolve_plugin_for_leave_task(task: LeaveAuditTask) -> str:
    leave_type = str(task.leave_type or "").upper()
    if task.attachments:
        explicit = task.attachments[0].plugin_name or task.attachments[0].metadata.get("plugin_name")
        if explicit:
            return str(explicit)
    return LEAVE_TYPE_PLUGIN_MAPPING.get(leave_type, "diagnosis_proof")
