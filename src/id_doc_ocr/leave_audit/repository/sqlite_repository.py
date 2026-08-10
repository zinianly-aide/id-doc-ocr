from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from id_doc_ocr.leave_audit.domain.async_status import CallbackStatus, DecisionStatus, OcrJobStatus
from id_doc_ocr.leave_audit.domain.config import ConfigKind, ConfigSnapshot, ConfigStatus
from id_doc_ocr.leave_audit.domain.enums import LeaveAuditStatus
from id_doc_ocr.leave_audit.domain.models import LeaveAttachment, LeaveAuditResult, LeaveAuditTask, LeaveReviewDecision, utc_now_iso
from id_doc_ocr.leave_audit.messaging.outbox import OutboxEvent

DEFAULT_DB_PATH = ".local/leave_audit.db"


SCHEMA_MIGRATIONS: tuple[tuple[int, str, str], ...] = (
    (
        1,
        "base_leave_audit_schema",
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
        """,
    ),
    (
        2,
        "prompt_config",
        """
        CREATE TABLE IF NOT EXISTS leave_audit_prompt_config (
            recognition_type TEXT NOT NULL,
            prompt_type TEXT NOT NULL,
            prompt_text TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (recognition_type, prompt_type)
        );
        """,
    ),
    (
        3,
        "orthogonal_async_statuses",
        """
        ALTER TABLE leave_audit_task ADD COLUMN ocr_status TEXT NOT NULL DEFAULT 'CREATED';
        ALTER TABLE leave_audit_task ADD COLUMN decision_status TEXT NOT NULL DEFAULT 'PENDING';
        ALTER TABLE leave_audit_task ADD COLUMN callback_status TEXT NOT NULL DEFAULT 'NOT_REQUIRED';
        ALTER TABLE leave_audit_task ADD COLUMN decision_version INTEGER NOT NULL DEFAULT 0;
        ALTER TABLE leave_audit_task ADD COLUMN ocr_profile_snapshot_id TEXT;
        ALTER TABLE leave_audit_task ADD COLUMN decision_policy_snapshot_id TEXT;
        ALTER TABLE leave_audit_task ADD COLUMN field_mapping_snapshot_id TEXT;
        ALTER TABLE leave_audit_task ADD COLUMN callback_policy_snapshot_id TEXT;
        ALTER TABLE leave_audit_result ADD COLUMN job_id TEXT;
        ALTER TABLE leave_audit_result ADD COLUMN attachment_id TEXT;
        ALTER TABLE leave_audit_result ADD COLUMN ocr_status TEXT NOT NULL DEFAULT 'SUCCEEDED';
        ALTER TABLE leave_audit_result ADD COLUMN decision_status TEXT;
        ALTER TABLE leave_audit_result ADD COLUMN callback_status TEXT NOT NULL DEFAULT 'NOT_REQUIRED';
        ALTER TABLE leave_audit_result ADD COLUMN decision_version INTEGER NOT NULL DEFAULT 0;
        ALTER TABLE leave_audit_result ADD COLUMN ocr_profile_snapshot_id TEXT;
        ALTER TABLE leave_audit_result ADD COLUMN decision_policy_snapshot_id TEXT;
        ALTER TABLE leave_audit_result ADD COLUMN field_mapping_snapshot_id TEXT;
        ALTER TABLE leave_audit_result ADD COLUMN callback_policy_snapshot_id TEXT;
        UPDATE leave_audit_task
        SET ocr_status = CASE WHEN status = 'PROCESSING' THEN 'PROCESSING' WHEN status IN ('PASS', 'REVIEW', 'REJECT') THEN 'SUCCEEDED' WHEN status = 'ERROR' THEN 'FAILED' ELSE 'CREATED' END,
            decision_status = CASE status WHEN 'PASS' THEN 'PASS' WHEN 'REVIEW' THEN 'REVIEW_REQUIRED' WHEN 'REJECT' THEN 'REJECT' ELSE 'PENDING' END,
            callback_status = CASE WHEN status = 'SYNCED' THEN 'SUCCEEDED' ELSE 'NOT_REQUIRED' END;
        UPDATE leave_audit_result
        SET ocr_status = CASE WHEN status = 'ERROR' THEN 'FAILED' ELSE 'SUCCEEDED' END,
            decision_status = CASE status WHEN 'PASS' THEN 'PASS' WHEN 'REVIEW' THEN 'REVIEW_REQUIRED' WHEN 'REJECT' THEN 'REJECT' ELSE NULL END,
            callback_status = CASE WHEN synced = 1 THEN 'SUCCEEDED' ELSE 'NOT_REQUIRED' END;
        """,
    ),
    (
        4,
        "versioned_config_snapshots",
        """
        CREATE TABLE IF NOT EXISTS leave_audit_config_version (
            version_id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            status TEXT NOT NULL,
            content_json TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            created_by TEXT NOT NULL,
            approved_by TEXT,
            published_at TEXT,
            change_reason TEXT,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_leave_audit_config_version_kind_status
            ON leave_audit_config_version (kind, status, created_at);
        """,
    ),
    (
        5,
        "task_outbox",
        """
        CREATE TABLE IF NOT EXISTS leave_audit_outbox_event (
            event_id TEXT PRIMARY KEY,
            aggregate_type TEXT NOT NULL,
            aggregate_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            published_at TEXT,
            attempt_count INTEGER NOT NULL DEFAULT 0,
            last_error TEXT,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_leave_audit_outbox_pending
            ON leave_audit_outbox_event (published_at, created_at);
        """,
    ),
)


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
            self._apply_migrations(conn)

    def _apply_migrations(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS leave_audit_schema_migration (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )
            """
        )
        applied_versions = {
            int(row["version"])
            for row in conn.execute("SELECT version FROM leave_audit_schema_migration").fetchall()
        }
        for version, name, sql in SCHEMA_MIGRATIONS:
            if version in applied_versions:
                continue
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO leave_audit_schema_migration (version, name, applied_at) VALUES (?, ?, ?)",
                (version, name, utc_now_iso()),
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
                (request_id, leave_type, employee_id, employee_name, leave_start_date, leave_end_date, status, attachments_json, raw_payload_json, created_at, updated_at,
                 ocr_status, decision_status, callback_status, decision_version, ocr_profile_snapshot_id, decision_policy_snapshot_id,
                 field_mapping_snapshot_id, callback_policy_snapshot_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(request_id) DO UPDATE SET
                    leave_type=excluded.leave_type,
                    employee_id=excluded.employee_id,
                    employee_name=excluded.employee_name,
                    leave_start_date=excluded.leave_start_date,
                    leave_end_date=excluded.leave_end_date,
                    status=excluded.status,
                    attachments_json=excluded.attachments_json,
                    raw_payload_json=excluded.raw_payload_json,
                    updated_at=excluded.updated_at,
                    ocr_status=excluded.ocr_status,
                    decision_status=excluded.decision_status,
                    callback_status=excluded.callback_status,
                    decision_version=excluded.decision_version,
                    ocr_profile_snapshot_id=excluded.ocr_profile_snapshot_id,
                    decision_policy_snapshot_id=excluded.decision_policy_snapshot_id,
                    field_mapping_snapshot_id=excluded.field_mapping_snapshot_id,
                    callback_policy_snapshot_id=excluded.callback_policy_snapshot_id
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
                    task.ocr_status.value,
                    task.decision_status.value,
                    task.callback_status.value,
                    task.decision_version,
                    task.ocr_profile_snapshot_id,
                    task.decision_policy_snapshot_id,
                    task.field_mapping_snapshot_id,
                    task.callback_policy_snapshot_id,
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
            now = utc_now_iso()
            if status is LeaveAuditStatus.SYNCED:
                conn.execute(
                    "UPDATE leave_audit_task SET callback_status = ?, updated_at = ? WHERE request_id = ?",
                    (CallbackStatus.SUCCEEDED.value, now, request_id),
                )
                return
            ocr_status = None
            decision_status = None
            if status is LeaveAuditStatus.PROCESSING:
                ocr_status = OcrJobStatus.PROCESSING.value
            elif status in {LeaveAuditStatus.PASS, LeaveAuditStatus.REVIEW, LeaveAuditStatus.REJECT}:
                ocr_status = OcrJobStatus.SUCCEEDED.value
                decision_status = {
                    LeaveAuditStatus.PASS: DecisionStatus.PASS.value,
                    LeaveAuditStatus.REVIEW: DecisionStatus.REVIEW_REQUIRED.value,
                    LeaveAuditStatus.REJECT: DecisionStatus.REJECT.value,
                }[status]
            elif status is LeaveAuditStatus.ERROR:
                ocr_status = OcrJobStatus.FAILED.value
            updates = ["status = ?", "updated_at = ?"]
            params: list[Any] = [status.value, now]
            if ocr_status is not None:
                updates.append("ocr_status = ?")
                params.append(ocr_status)
            if decision_status is not None:
                updates.append("decision_status = ?")
                params.append(decision_status)
            params.append(request_id)
            conn.execute(f"UPDATE leave_audit_task SET {', '.join(updates)} WHERE request_id = ?", tuple(params))

    def update_callback_status(self, request_id: str, status: CallbackStatus) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE leave_audit_task SET callback_status = ?, updated_at = ? WHERE request_id = ?",
                (status.value, utc_now_iso(), request_id),
            )

    def save_result(self, result: LeaveAuditResult) -> None:
        result.updated_at = utc_now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO leave_audit_result
                (request_id, status, plugin_name, analysis_json, verification_json, error_message, synced, created_at, updated_at,
                 job_id, attachment_id, ocr_status, decision_status, callback_status, decision_version, ocr_profile_snapshot_id,
                 decision_policy_snapshot_id, field_mapping_snapshot_id, callback_policy_snapshot_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(request_id) DO UPDATE SET
                    status=excluded.status,
                    plugin_name=excluded.plugin_name,
                    analysis_json=excluded.analysis_json,
                    verification_json=excluded.verification_json,
                    error_message=excluded.error_message,
                    synced=excluded.synced,
                    updated_at=excluded.updated_at,
                    job_id=excluded.job_id,
                    attachment_id=excluded.attachment_id,
                    ocr_status=excluded.ocr_status,
                    decision_status=excluded.decision_status,
                    callback_status=excluded.callback_status,
                    decision_version=excluded.decision_version,
                    ocr_profile_snapshot_id=excluded.ocr_profile_snapshot_id,
                    decision_policy_snapshot_id=excluded.decision_policy_snapshot_id,
                    field_mapping_snapshot_id=excluded.field_mapping_snapshot_id,
                    callback_policy_snapshot_id=excluded.callback_policy_snapshot_id
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
                    result.job_id,
                    result.attachment_id,
                    result.ocr_status.value,
                    result.decision_status.value if result.decision_status else None,
                    result.callback_status.value,
                    result.decision_version,
                    result.ocr_profile_snapshot_id,
                    result.decision_policy_snapshot_id,
                    result.field_mapping_snapshot_id,
                    result.callback_policy_snapshot_id,
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
            job_id=row["job_id"],
            attachment_id=row["attachment_id"],
            ocr_status=OcrJobStatus(row["ocr_status"]),
            decision_status=DecisionStatus(row["decision_status"]) if row["decision_status"] else None,
            callback_status=CallbackStatus(row["callback_status"]),
            decision_version=int(row["decision_version"]),
            ocr_profile_snapshot_id=row["ocr_profile_snapshot_id"],
            decision_policy_snapshot_id=row["decision_policy_snapshot_id"],
            field_mapping_snapshot_id=row["field_mapping_snapshot_id"],
            callback_policy_snapshot_id=row["callback_policy_snapshot_id"],
        )

    def save_review(self, decision: LeaveReviewDecision) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO leave_audit_review (request_id, decision, reviewer, comment, created_at) VALUES (?, ?, ?, ?, ?)",
                (decision.request_id, decision.decision.value, decision.reviewer, decision.comment, decision.created_at),
            )
            decision_status = {
                LeaveAuditStatus.PASS: DecisionStatus.PASS.value,
                LeaveAuditStatus.REVIEW: DecisionStatus.REVIEW_REQUIRED.value,
                LeaveAuditStatus.REJECT: DecisionStatus.REJECT.value,
            }.get(decision.decision)
            conn.execute(
                "UPDATE leave_audit_task SET status = ?, decision_status = COALESCE(?, decision_status), decision_version = decision_version + 1, updated_at = ? WHERE request_id = ?",
                (decision.decision.value, decision_status, utc_now_iso(), decision.request_id),
            )

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

    def get_prompt_configs(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT recognition_type, prompt_type, prompt_text, enabled, updated_at
                FROM leave_audit_prompt_config
                ORDER BY recognition_type, prompt_type
                """
            ).fetchall()
        return [
            {
                "recognition_type": row["recognition_type"],
                "prompt_type": row["prompt_type"],
                "prompt_text": row["prompt_text"],
                "enabled": bool(row["enabled"]),
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]

    def get_effective_prompt_texts(self, recognition_type: str) -> dict[str, str]:
        normalized = str(recognition_type).strip()
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT recognition_type, prompt_type, prompt_text
                FROM leave_audit_prompt_config
                WHERE enabled = 1 AND recognition_type IN ('*', ?)
                ORDER BY CASE WHEN recognition_type = '*' THEN 0 ELSE 1 END, prompt_type
                """,
                (normalized,),
            ).fetchall()
        prompts: dict[str, str] = {}
        for row in rows:
            text = str(row["prompt_text"] or "").strip()
            if text:
                prompts[str(row["prompt_type"])] = text
        return prompts

    def save_prompt_config(self, recognition_type: str, prompt_type: str, prompt_text: str, enabled: bool = True) -> None:
        normalized_recognition_type = str(recognition_type).strip()
        normalized_prompt_type = str(prompt_type).strip()
        if not normalized_recognition_type:
            raise ValueError("recognition_type is required")
        if not normalized_prompt_type:
            raise ValueError("prompt_type is required")
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO leave_audit_prompt_config (recognition_type, prompt_type, prompt_text, enabled, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(recognition_type, prompt_type) DO UPDATE SET
                    prompt_text=excluded.prompt_text,
                    enabled=excluded.enabled,
                    updated_at=excluded.updated_at
                """,
                (normalized_recognition_type, normalized_prompt_type, prompt_text, 1 if enabled else 0, utc_now_iso()),
            )

    def save_config_snapshot(self, snapshot: ConfigSnapshot) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO leave_audit_config_version
                (version_id, kind, status, content_json, content_hash, created_by, approved_by, published_at, change_reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(version_id) DO UPDATE SET
                    kind=excluded.kind,
                    status=excluded.status,
                    content_json=excluded.content_json,
                    content_hash=excluded.content_hash,
                    created_by=excluded.created_by,
                    approved_by=excluded.approved_by,
                    published_at=excluded.published_at,
                    change_reason=excluded.change_reason
                """,
                (
                    snapshot.version_id,
                    snapshot.kind.value,
                    snapshot.status.value,
                    _json(snapshot.content),
                    snapshot.content_hash,
                    snapshot.created_by,
                    snapshot.approved_by,
                    snapshot.published_at,
                    snapshot.change_reason,
                    snapshot.created_at,
                ),
            )

    def get_config_snapshot(self, version_id: str) -> ConfigSnapshot | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM leave_audit_config_version WHERE version_id = ?", (version_id,)).fetchone()
        if not row:
            return None
        return ConfigSnapshot(
            version_id=row["version_id"],
            kind=ConfigKind(row["kind"]),
            status=ConfigStatus(row["status"]),
            content=_loads(row["content_json"], {}),
            content_hash=row["content_hash"],
            created_by=row["created_by"],
            approved_by=row["approved_by"],
            published_at=row["published_at"],
            change_reason=row["change_reason"],
            created_at=row["created_at"],
        )

    def list_config_snapshots(self, kind: ConfigKind | None = None) -> list[ConfigSnapshot]:
        with self.connect() as conn:
            if kind is None:
                rows = conn.execute("SELECT * FROM leave_audit_config_version ORDER BY created_at DESC").fetchall()
            else:
                rows = conn.execute("SELECT * FROM leave_audit_config_version WHERE kind = ? ORDER BY created_at DESC", (kind.value,)).fetchall()
        return [self.get_config_snapshot(row["version_id"]) for row in rows if row is not None]

    def enqueue_outbox_event(self, event: OutboxEvent) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO leave_audit_outbox_event
                (event_id, aggregate_type, aggregate_id, event_type, payload_json, published_at, attempt_count, last_error, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(event_id) DO NOTHING
                """,
                (
                    event.event_id,
                    event.aggregate_type,
                    event.aggregate_id,
                    event.event_type,
                    _json(event.payload),
                    event.published_at,
                    event.attempt_count,
                    event.last_error,
                    event.created_at,
                ),
            )

    def list_pending_outbox(self, limit: int = 100) -> list[OutboxEvent]:
        if limit < 1:
            return []
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM leave_audit_outbox_event WHERE published_at IS NULL ORDER BY created_at ASC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            OutboxEvent(
                event_id=row["event_id"],
                aggregate_type=row["aggregate_type"],
                aggregate_id=row["aggregate_id"],
                event_type=row["event_type"],
                payload=_loads(row["payload_json"], {}),
                published_at=row["published_at"],
                attempt_count=int(row["attempt_count"]),
                last_error=row["last_error"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def mark_outbox_published(self, event_id: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE leave_audit_outbox_event SET published_at = ?, attempt_count = attempt_count + 1, last_error = NULL WHERE event_id = ?",
                (utc_now_iso(), event_id),
            )

    def mark_outbox_failed(self, event_id: str, error: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE leave_audit_outbox_event SET attempt_count = attempt_count + 1, last_error = ? WHERE event_id = ?",
                (error, event_id),
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
            ocr_status=OcrJobStatus(row["ocr_status"]),
            decision_status=DecisionStatus(row["decision_status"]),
            callback_status=CallbackStatus(row["callback_status"]),
            decision_version=int(row["decision_version"]),
            ocr_profile_snapshot_id=row["ocr_profile_snapshot_id"],
            decision_policy_snapshot_id=row["decision_policy_snapshot_id"],
            field_mapping_snapshot_id=row["field_mapping_snapshot_id"],
            callback_policy_snapshot_id=row["callback_policy_snapshot_id"],
        )
