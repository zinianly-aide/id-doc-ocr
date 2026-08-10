from __future__ import annotations

from id_doc_ocr.leave_audit.adapters.factory import create_leave_system_adapter
from id_doc_ocr.leave_audit.repository.factory import create_leave_audit_repository
from id_doc_ocr.leave_audit.worker.callback import CallbackOutboxWorker


def main() -> None:
    worker = CallbackOutboxWorker(create_leave_audit_repository(), create_leave_system_adapter())
    worker.run_forever()
