from __future__ import annotations

import json
import os
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from id_doc_ocr.leave_audit.adapters.base import LeaveSystemAdapter
from id_doc_ocr.leave_audit.adapters.field_mapping import normalize_pending_item
from id_doc_ocr.leave_audit.domain.enums import LeaveAuditStatus
from id_doc_ocr.leave_audit.domain.models import LeaveAttachment, LeaveAuditResult, LeaveAuditTask

ORACLE_TNA_DB_ENV = "ID_DOC_OCR_ORACLE_TNA_DB"
ORACLE_TNA_TABLE_ENV = "ID_DOC_OCR_ORACLE_TNA_TABLE"
ORACLE_TNA_DSN_ENV = "ID_DOC_OCR_ORACLE_TNA_DSN"
ORACLE_TNA_USER_ENV = "ID_DOC_OCR_ORACLE_TNA_USER"
ORACLE_TNA_PASSWORD_ENV = "ID_DOC_OCR_ORACLE_TNA_PASSWORD"
ORACLE_TNA_DOC_TABLE_ENV = "ID_DOC_OCR_ORACLE_TNA_DOC_TABLE"
DEFAULT_DOC_CONTENT_TABLE = "F10HRMGR.TBCN_DOC_CONTENT"
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?$")


def oracle_tna_sync_configured() -> bool:
    return bool(os.getenv(ORACLE_TNA_DB_ENV))


@dataclass(frozen=True, slots=True)
class OracleDocumentContent:
    doc_content_index: str
    mime_type: str
    doc_size: int | None
    is_archive: str | int | None
    content: bytes


def _read_lob_or_bytes(value: Any) -> bytes:
    if hasattr(value, "read"):
        value = value.read()
    if isinstance(value, memoryview):
        return value.tobytes()
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    if isinstance(value, str):
        return value.encode("utf-8")
    raise TypeError(f"unsupported Oracle document content type: {type(value).__name__}")


def _normalize_doc_content_index(attachment_url: str) -> str:
    value = str(attachment_url).strip()
    for prefix in ("oracle-tna://", "tna-doc://", "DOC_CONTENT_INDEX:"):
        if value.startswith(prefix):
            return value[len(prefix):].strip()
    return value


class OracleDocumentContentService:
    def __init__(
        self,
        db_path: str | Path | None = None,
        table_name: str | None = None,
        dsn: str | None = None,
        user: str | None = None,
        password: str | None = None,
    ) -> None:
        self.db_path = Path(db_path or os.getenv(ORACLE_TNA_DB_ENV) or "") if db_path or os.getenv(ORACLE_TNA_DB_ENV) else None
        self.table_name = table_name or os.getenv(ORACLE_TNA_DOC_TABLE_ENV) or DEFAULT_DOC_CONTENT_TABLE
        self.dsn = dsn or os.getenv(ORACLE_TNA_DSN_ENV)
        self.user = user or os.getenv(ORACLE_TNA_USER_ENV)
        self.password = password or os.getenv(ORACLE_TNA_PASSWORD_ENV)
        if not _IDENTIFIER_RE.fullmatch(self.table_name):
            raise ValueError(f"{ORACLE_TNA_DOC_TABLE_ENV} must be a simple SQL identifier or schema.table")

    def fetch(self, doc_content_index: str) -> OracleDocumentContent:
        index = _normalize_doc_content_index(doc_content_index)
        if not index:
            raise ValueError("DOC_CONTENT_INDEX is required")
        if self.db_path:
            return self._fetch_sqlite(index)
        return self._fetch_oracle(index)

    def _fetch_sqlite(self, doc_content_index: str) -> OracleDocumentContent:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                f"""
                SELECT DOC_CONTENT_INDEX, MIME_TYPE, DOC_SIZE, IS_ARCHIVE, CONTENT
                FROM {self.table_name}
                WHERE DOC_CONTENT_INDEX = ? AND MIME_TYPE != 'text/xml'
                """,
                (doc_content_index,),
            ).fetchone()
        if row is None:
            raise FileNotFoundError(f"Oracle TNA document content not found or XML-only: {doc_content_index}")
        return self._row_to_content(dict(row))

    def _fetch_oracle(self, doc_content_index: str) -> OracleDocumentContent:
        if not (self.dsn and self.user and self.password):
            raise ValueError(f"{ORACLE_TNA_DSN_ENV}, {ORACLE_TNA_USER_ENV}, and {ORACLE_TNA_PASSWORD_ENV} are required")
        try:
            import oracledb  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("Install optional dependency 'oracledb' to read Oracle TNA document content") from exc

        with oracledb.connect(user=self.user, password=self.password, dsn=self.dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT DOC_CONTENT_INDEX, MIME_TYPE, DOC_SIZE, IS_ARCHIVE, CONTENT
                    FROM {self.table_name}
                    WHERE DOC_CONTENT_INDEX = :doc_content_index AND MIME_TYPE != 'text/xml'
                    """,
                    doc_content_index=doc_content_index,
                )
                row = cursor.fetchone()
                columns = [column[0] for column in cursor.description or []]
        if row is None:
            raise FileNotFoundError(f"Oracle TNA document content not found or XML-only: {doc_content_index}")
        return self._row_to_content(dict(zip(columns, row)))

    def _row_to_content(self, row: dict[str, Any]) -> OracleDocumentContent:
        return OracleDocumentContent(
            doc_content_index=str(row["DOC_CONTENT_INDEX"]),
            mime_type=str(row["MIME_TYPE"]),
            doc_size=int(row["DOC_SIZE"]) if row.get("DOC_SIZE") is not None else None,
            is_archive=row.get("IS_ARCHIVE"),
            content=_read_lob_or_bytes(row["CONTENT"]),
        )


class OracleTNASource:
    def __init__(self, db_path: str | Path | None = None, table_name: str | None = None) -> None:
        self.db_path = Path(db_path or os.getenv(ORACLE_TNA_DB_ENV) or "")
        self.table_name = table_name or os.getenv(ORACLE_TNA_TABLE_ENV) or "tna_leave_audit_task"
        if not self.db_path:
            raise ValueError(f"{ORACLE_TNA_DB_ENV} is required")
        if not _IDENTIFIER_RE.fullmatch(self.table_name):
            raise ValueError(f"{ORACLE_TNA_TABLE_ENV} must be a simple SQL identifier or schema.table")

    def fetch_tasks(self) -> list[LeaveAuditTask]:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(f"SELECT * FROM {self.table_name}").fetchall()
        return [self._task_from_row(row) for row in rows]

    def _task_from_row(self, row: sqlite3.Row) -> LeaveAuditTask:
        payload = dict(row)
        raw_payload = self._raw_payload(payload)
        normalized = normalize_pending_item(raw_payload)
        attachments = [
            LeaveAttachment(
                attachment_id=str(item["attachment_id"]),
                attachment_url=str(item["attachment_url"]),
                filename=item.get("attachment_name"),
                content_type=item.get("content_type"),
                plugin_name=item.get("plugin_name"),
                metadata=dict(item.get("metadata") or {}),
            )
            for item in normalized["attachments"]
        ]
        return LeaveAuditTask(
            request_id=str(normalized["request_id"]),
            leave_type=str(normalized["leave_type"]),
            employee_id=normalized.get("employee_id"),
            employee_name=str(normalized["employee_name"]),
            leave_start_date=normalized.get("leave_start_date"),
            leave_end_date=normalized.get("leave_end_date"),
            status=LeaveAuditStatus(normalized.get("status") or "PENDING"),
            attachments=attachments,
            raw_payload=raw_payload,
        )

    def _raw_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        if isinstance(payload.get("payload_json"), str) and payload["payload_json"].strip():
            loaded = json.loads(payload["payload_json"])
            if not isinstance(loaded, dict):
                raise ValueError("payload_json must contain an object")
            return loaded
        attachments_json = payload.pop("attachments_json", None)
        if isinstance(attachments_json, str) and attachments_json.strip():
            payload["attachments"] = json.loads(attachments_json)
        return payload


class OracleTNALeaveSystemAdapter(LeaveSystemAdapter):
    def __init__(
        self,
        source: OracleTNASource | None = None,
        document_service: OracleDocumentContentService | None = None,
    ) -> None:
        self.source = source or OracleTNASource()
        self.document_service = document_service or OracleDocumentContentService()
        self.pushed_results: list[LeaveAuditResult] = []

    def fetch_pending_attachments(self) -> list[LeaveAuditTask]:
        return self.source.fetch_tasks()

    def download_attachment(self, attachment_url: str) -> bytes:
        return self.document_service.fetch(attachment_url).content

    def push_audit_result(self, result: LeaveAuditResult) -> None:
        self.pushed_results.append(result)
