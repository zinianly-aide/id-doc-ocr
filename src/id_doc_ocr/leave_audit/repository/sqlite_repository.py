from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from id_doc_ocr.leave_audit.domain.enums import LeaveAuditStatus
from id_doc_ocr.leave_audit.domain.models import LeaveAttachment, LeaveAuditResult, LeaveAuditTask, LeaveReviewDecision, utc_now_iso

DEFAULT_DB_PATH = ".local/leave_audit.db"


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True)


def _loads(text: str | None, default: Any) -> Any:
    if not text:
        return default
    return json.loads(text)


class SQLiteRepository:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path or os.getenv("ID_DOC_OCR_LEAVE_AUDIT_DB") or DEFAULT_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS leave_audit_task (
                    request_id TEXT PRIMARY KEY,
                    leave_type TEXT NOT NULL,
                    employee_id TEXT,
                    employee_name TEXT NOT NULL,
                    leave_start_date TEXT,
                    leave_end_date TEXT,
                    status TEXT NOT NULL,
                    attachments_json TEXT NOT NULL,
                    raw_payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS leave_audit_result (
                    request_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    plugin_name TEXT,
                    analysis_json TEXT NOT NULL,
                    verification_json TEXT NOT NULL,
                    error_message TEXT,
                    synced INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS leave_audit_review (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    reviewer TEXT NOT NULL,
                    comment TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS leave_audit_field_mapping (
                    canonical_field TEXT PRIMARY KEY,
                    candidates_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS leave_audit_rule_config (
                    leave_type TEXT PRIMARY KEY,
                    prompt_text TEXT NOT NULL,
                    rules_json TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    updated_at TEXT NOT NULL
                );
                """
            )

    def save_task(self, task: LeaveAuditTask) -> None:
        now = utc_now_iso()
        task.updated_at = now
        attachments = [
            {
                "attachment_id": att.attachment_id,
                "attachment_url": att.attachment_url,
                "filename": att.filename,
                "content_type": att.content_type,
                "plugin_name": att.plugin_name,
                "metadata": att.metadata,
            }
            for att in task.attachments
        ]
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO leave_audit_task
                (request_id, leave_type, employee_id, employee_name, leave_start_date, leave_end_date, status, attachments_json, raw_payload_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(request_id) DO UPDATE SET
                    leave_type=excluded.leave_type,
                    employee_id=excluded.employee_id,
                    employee_name=excluded.employee_name,
                    leave_start_date=excluded.leave_start_date,
                    leave_end_date=excluded.leave_end_date,
                    status=excluded.status,
                    attachments_json=excluded.attachments_json,
                    raw_payload_json=excluded.raw_payload_json,
                    updated_at=excluded.updated_at
                """,
                (
                    task.request_id,
                    task.leave_type,
                    task.employee_id,
                    task.employee_name,
                    task.leave_start_date,
                    task.leave_end_date,
                    task.status.value if isinstance(task.status, LeaveAuditStatus) else str(task.status),
                    _json(attachments),
                    _json(task.raw_payload),
                    task.created_at,
                    task.updated_at,
                ),
            )

    def get_task(self, request_id: str) -> LeaveAuditTask | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM leave_audit_task WHERE request_id = ?", (request_id,)).fetchone()
        return self._row_to_task(row) if row else None

    def list_tasks(self, status: str | None = None) -> list[LeaveAuditTask]:
        with self.connect() as conn:
            if status:
                rows = conn.execute("SELECT * FROM leave_audit_task WHERE status = ? ORDER BY created_at DESC", (status,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM leave_audit_task ORDER BY created_at DESC").fetchall()
        return [self._row_to_task(row) for row in rows]

    def update_task_status(self, request_id: str, status: LeaveAuditStatus) -> None:
        with self.connect() as conn:
            conn.execute("UPDATE leave_audit_task SET status = ?, updated_at = ? WHERE request_id = ?", (status.value, utc_now_iso(), request_id))

    def save_result(self, result: LeaveAuditResult) -> None:
        result.updated_at = utc_now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO leave_audit_result
                (request_id, status, plugin_name, analysis_json, verification_json, error_message, synced, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(request_id) DO UPDATE SET
                    status=excluded.status,
                    plugin_name=excluded.plugin_name,
                    analysis_json=excluded.analysis_json,
                    verification_json=excluded.verification_json,
                    error_message=excluded.error_message,
                    synced=excluded.synced,
                    updated_at=excluded.updated_at
                """,
                (
                    result.request_id,
                    result.status.value if isinstance(result.status, LeaveAuditStatus) else str(result.status),
                    result.plugin_name,
                    _json(result.analysis_json),
                    _json(result.verification_json),
                    result.error_message,
                    1 if result.synced else 0,
                    result.created_at,
                    result.updated_at,
                ),
            )

    def get_result(self, request_id: str) -> LeaveAuditResult | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM leave_audit_result WHERE request_id = ?", (request_id,)).fetchone()
        if not row:
            return None
        return LeaveAuditResult(
            request_id=row["request_id"],
            status=LeaveAuditStatus(row["status"]),
            plugin_name=row["plugin_name"],
            analysis_json=_loads(row["analysis_json"], {}),
            verification_json=_loads(row["verification_json"], {}),
            error_message=row["error_message"],
            synced=bool(row["synced"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def save_review(self, decision: LeaveReviewDecision) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO leave_audit_review (request_id, decision, reviewer, comment, created_at) VALUES (?, ?, ?, ?, ?)",
                (decision.request_id, decision.decision.value, decision.reviewer, decision.comment, decision.created_at),
            )
            conn.execute("UPDATE leave_audit_task SET status = ?, updated_at = ? WHERE request_id = ?", (decision.decision.value, utc_now_iso(), decision.request_id))

    def list_reviews(self, request_id: str) -> list[LeaveReviewDecision]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM leave_audit_review WHERE request_id = ? ORDER BY created_at ASC", (request_id,)).fetchall()
        return [LeaveReviewDecision(request_id=row["request_id"], decision=LeaveAuditStatus(row["decision"]), reviewer=row["reviewer"], comment=row["comment"], created_at=row["created_at"]) for row in rows]

    def stats(self) -> dict[str, int]:
        with self.connect() as conn:
            rows = conn.execute("SELECT status, COUNT(*) AS count FROM leave_audit_task GROUP BY status").fetchall()
        return {row["status"]: row["count"] for row in rows}

    def get_field_mappings(self) -> dict[str, list[str]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT canonical_field, candidates_json FROM leave_audit_field_mapping ORDER BY canonical_field").fetchall()
        return {row["canonical_field"]: [str(item) for item in _loads(row["candidates_json"], []) if str(item).strip()] for row in rows}

    def save_field_mapping(self, canonical_field: str, candidates: list[str]) -> None:
        normalized = [str(candidate).strip() for candidate in candidates if str(candidate).strip()]
        if not canonical_field.strip():
            raise ValueError("canonical_field is required")
        if not normalized:
            raise ValueError("candidates must not be empty")
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO leave_audit_field_mapping (canonical_field, candidates_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(canonical_field) DO UPDATE SET
                    candidates_json=excluded.candidates_json,
                    updated_at=excluded.updated_at
                """,
                (canonical_field.strip(), _json(normalized), utc_now_iso()),
            )

    def get_rule_configs(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT leave_type, prompt_text, rules_json, enabled, updated_at FROM leave_audit_rule_config ORDER BY leave_type").fetchall()
        return [
            {
                "leave_type": row["leave_type"],
                "prompt_text": row["prompt_text"],
                "rules": _loads(row["rules_json"], []),
                "enabled": bool(row["enabled"]),
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]

    def get_rule_config(self, leave_type: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT leave_type, prompt_text, rules_json, enabled, updated_at FROM leave_audit_rule_config WHERE leave_type = ?",
                (str(leave_type).upper(),),
            ).fetchone()
        if not row:
            return None
        return {
            "leave_type": row["leave_type"],
            "prompt_text": row["prompt_text"],
            "rules": _loads(row["rules_json"], []),
            "enabled": bool(row["enabled"]),
            "updated_at": row["updated_at"],
        }

    def save_rule_config(self, leave_type: str, prompt_text: str, rules: list[dict[str, Any]], enabled: bool = True) -> None:
        normalized_leave_type = str(leave_type).upper().strip()
        if not normalized_leave_type:
            raise ValueError("leave_type is required")
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO leave_audit_rule_config (leave_type, prompt_text, rules_json, enabled, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(leave_type) DO UPDATE SET
                    prompt_text=excluded.prompt_text,
                    rules_json=excluded.rules_json,
                    enabled=excluded.enabled,
                    updated_at=excluded.updated_at
                """,
                (normalized_leave_type, prompt_text, _json(rules), 1 if enabled else 0, utc_now_iso()),
            )

    def _row_to_task(self, row: sqlite3.Row) -> LeaveAuditTask:
        attachments = [
            LeaveAttachment(
                attachment_id=str(item.get("attachment_id")),
                attachment_url=str(item.get("attachment_url")),
                filename=item.get("filename"),
                content_type=item.get("content_type"),
                plugin_name=item.get("plugin_name"),
                metadata=dict(item.get("metadata") or {}),
            )
            for item in _loads(row["attachments_json"], [])
        ]
        return LeaveAuditTask(
            request_id=row["request_id"],
            leave_type=row["leave_type"],
            employee_id=row["employee_id"],
            employee_name=row["employee_name"],
            leave_start_date=row["leave_start_date"],
            leave_end_date=row["leave_end_date"],
            status=LeaveAuditStatus(row["status"]),
            attachments=attachments,
            raw_payload=_loads(row["raw_payload_json"], {}),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
