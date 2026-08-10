from __future__ import annotations

from id_doc_ocr.leave_audit.adapters.factory import create_leave_system_adapter
from id_doc_ocr.leave_audit.repository.sqlite_repository import SQLiteRepository
from id_doc_ocr.leave_audit.storage.factory import create_object_storage
from id_doc_ocr.leave_audit.worker.callback import CallbackOutboxWorker


def main() -> None:
    worker = CallbackOutboxWorker(SQLiteRepository(), create_leave_system_adapter())
    worker.process_pending()
