from __future__ import annotations

import os

from id_doc_ocr.leave_audit.repository.base import LeaveAuditRepository
from id_doc_ocr.leave_audit.repository.sqlite_repository import SQLiteRepository


def create_leave_audit_repository() -> LeaveAuditRepository:
    """Select production PostgreSQL when DATABASE_URL is configured.

    SQLite remains the default for local development and unit tests.
    """
    dsn = os.getenv("DATABASE_URL") or os.getenv("ID_DOC_OCR_DATABASE_URL")
    if dsn:
        from id_doc_ocr.leave_audit.repository.postgres_repository import PostgresRepository

        return PostgresRepository(dsn)
    return SQLiteRepository()
