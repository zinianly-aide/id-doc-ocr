from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Callable

from id_doc_ocr.leave_audit.domain.async_status import CallbackStatus, DecisionStatus, OcrJobStatus
from id_doc_ocr.leave_audit.domain.config import ConfigKind, ConfigSnapshot, ConfigStatus
from id_doc_ocr.leave_audit.domain.enums import LeaveAuditStatus
from id_doc_ocr.leave_audit.domain.models import LeaveAttachment, LeaveAuditResult, LeaveAuditTask, LeaveReviewDecision, utc_now_iso
from id_doc_ocr.leave_audit.messaging.outbox import CallbackOutboxItem, OutboxEvent


def _iso(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


class PostgresRepository:
    """PostgreSQL implementation of the Leave Audit persistence port.

    The driver is optional so local mock/SQLite development remains lightweight.
    Run ``scripts/migrate_postgres.py`` before selecting this repository in a
    production process.
    """

    def __init__(self, dsn: str | None = None, connect_factory: Callable[..., Any] | None = None) -> None:
        self.dsn = dsn or os.getenv("DATABASE_URL") or os.getenv("ID_DOC_OCR_DATABASE_URL")
        if not self.dsn and connect_factory is None:
            raise ValueError("DATABASE_URL or ID_DOC_OCR_DATABASE_URL is required")
        self._connect_factory = connect_factory
        self._jsonb = None

    def connect(self) -> Any:
        if self._connect_factory is not None:
            return self._connect_factory(self.dsn)
        try:
            import psycopg
            from psycopg.rows import dict_row
            from psycopg.types.json import Jsonb
        except ImportError as exc:  # pragma: no cover - optional runtime dependency
            raise RuntimeError("PostgreSQL support requires the 'postgres' extra") from exc
        self._jsonb = Jsonb
        return psycopg.connect(self.dsn, row_factory=dict_row)

    def _json(self, value: Any) -> Any:
        if self._jsonb is None:
            try:
                from psycopg.types.json import Jsonb
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError("PostgreSQL support requires the 'postgres' extra") from exc
            self._jsonb = Jsonb
        return self._jsonb(value)

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
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO leave_audit_task
                (request_id, leave_type, employee_id, employee_name, leave_start_date, leave_end_date, status,
                 ocr_status, decision_status, callback_status, decision_version, ocr_profile_snapshot_id,
                 decision_policy_snapshot_id, field_mapping_snapshot_id, callback_policy_snapshot_id,
                 attachments_json, raw_payload_json, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT(request_id) DO UPDATE SET
                    leave_type=EXCLUDED.leave_type,
                    employee_id=EXCLUDED.employee_id,
                    employee_name=EXCLUDED.employee_name,
                    leave_start_date=EXCLUDED.leave_start_date,
                    leave_end_date=EXCLUDED.leave_end_date,
                    status=EXCLUDED.status,
                    ocr_status=EXCLUDED.ocr_status,
                    decision_status=EXCLUDED.decision_status,
                    callback_status=EXCLUDED.callback_status,
                    decision_version=EXCLUDED.decision_version,
                    ocr_profile_snapshot_id=EXCLUDED.ocr_profile_snapshot_id,
                    decision_policy_snapshot_id=EXCLUDED.decision_policy_snapshot_id,
                    field_mapping_snapshot_id=EXCLUDED.field_mapping_snapshot_id,
                    callback_policy_snapshot_id=EXCLUDED.callback_policy_snapshot_id,
                    attachments_json=EXCLUDED.attachments_json,
                    raw_payload_json=EXCLUDED.raw_payload_json,
                    updated_at=EXCLUDED.updated_at
                """,
                (
                    task.request_id,
                    task.leave_type,
                    task.employee_id,
                    task.employee_name,
                    task.leave_start_date,
                    task.leave_end_date,
                    task.status.value,
                    task.ocr_status.value,
                    task.decision_status.value,
                    task.callback_status.value,
                    task.decision_version,
                    task.ocr_profile_snapshot_id,
                    task.decision_policy_snapshot_id,
                    task.field_mapping_snapshot_id,
                    task.callback_policy_snapshot_id,
                    self._json(attachments),
                    self._json(task.raw_payload),
                    task.created_at,
                    task.updated_at,
                ),
            )

    def get_task(self, request_id: str) -> LeaveAuditTask | None:
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM leave_audit_task WHERE request_id = %s", (request_id,))
            row = cur.fetchone()
        return self._row_to_task(row) if row else None

    def list_tasks(self, status: str | None = None) -> list[LeaveAuditTask]:
        with self.connect() as conn, conn.cursor() as cur:
            if status:
                cur.execute("SELECT * FROM leave_audit_task WHERE status = %s ORDER BY created_at DESC", (status,))
            else:
                cur.execute("SELECT * FROM leave_audit_task ORDER BY created_at DESC")
            rows = cur.fetchall()
        return [self._row_to_task(row) for row in rows]

    def update_task_status(self, request_id: str, status: LeaveAuditStatus) -> None:
        now = utc_now_iso()
        if status is LeaveAuditStatus.SYNCED:
            self.update_callback_status(request_id, CallbackStatus.SUCCEEDED)
            return
        updates = ["status = %s", "updated_at = %s"]
        params: list[Any] = [status.value, now]
        if status is LeaveAuditStatus.PROCESSING:
            updates.append("ocr_status = %s")
            params.append(OcrJobStatus.PROCESSING.value)
        elif status in {LeaveAuditStatus.PASS, LeaveAuditStatus.REVIEW, LeaveAuditStatus.REJECT}:
            updates.extend(["ocr_status = %s", "decision_status = %s"])
            params.extend(
                [
                    OcrJobStatus.SUCCEEDED.value,
                    {
                        LeaveAuditStatus.PASS: DecisionStatus.PASS.value,
                        LeaveAuditStatus.REVIEW: DecisionStatus.REVIEW_REQUIRED.value,
                        LeaveAuditStatus.REJECT: DecisionStatus.REJECT.value,
                    }[status],
                ]
            )
        elif status is LeaveAuditStatus.ERROR:
            updates.append("ocr_status = %s")
            params.append(OcrJobStatus.FAILED.value)
        params.append(request_id)
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute(f"UPDATE leave_audit_task SET {', '.join(updates)} WHERE request_id = %s", tuple(params))

    def update_callback_status(self, request_id: str, status: CallbackStatus) -> None:
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE leave_audit_task SET callback_status = %s, updated_at = %s WHERE request_id = %s",
                (status.value, utc_now_iso(), request_id),
            )

    def save_result(self, result: LeaveAuditResult) -> None:
        result.updated_at = utc_now_iso()
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO leave_audit_result
                (request_id, job_id, attachment_id, status, ocr_status, decision_status, callback_status, decision_version,
                 plugin_name, analysis_json, verification_json, error_message, synced, ocr_profile_snapshot_id,
                 decision_policy_snapshot_id, field_mapping_snapshot_id, callback_policy_snapshot_id, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT(request_id) DO UPDATE SET
                    job_id=EXCLUDED.job_id,
                    attachment_id=EXCLUDED.attachment_id,
                    status=EXCLUDED.status,
                    ocr_status=EXCLUDED.ocr_status,
                    decision_status=EXCLUDED.decision_status,
                    callback_status=EXCLUDED.callback_status,
                    decision_version=EXCLUDED.decision_version,
                    plugin_name=EXCLUDED.plugin_name,
                    analysis_json=EXCLUDED.analysis_json,
                    verification_json=EXCLUDED.verification_json,
                    error_message=EXCLUDED.error_message,
                    synced=EXCLUDED.synced,
                    ocr_profile_snapshot_id=EXCLUDED.ocr_profile_snapshot_id,
                    decision_policy_snapshot_id=EXCLUDED.decision_policy_snapshot_id,
                    field_mapping_snapshot_id=EXCLUDED.field_mapping_snapshot_id,
                    callback_policy_snapshot_id=EXCLUDED.callback_policy_snapshot_id,
                    updated_at=EXCLUDED.updated_at
                """,
                (
                    result.request_id,
                    result.job_id,
                    result.attachment_id,
                    result.status.value,
                    result.ocr_status.value,
                    result.decision_status.value if result.decision_status else None,
                    result.callback_status.value,
                    result.decision_version,
                    result.plugin_name,
                    self._json(result.analysis_json),
                    self._json(result.verification_json),
                    result.error_message,
                    result.synced,
                    result.ocr_profile_snapshot_id,
                    result.decision_policy_snapshot_id,
                    result.field_mapping_snapshot_id,
                    result.callback_policy_snapshot_id,
                    result.created_at,
                    result.updated_at,
                ),
            )

    def get_result(self, request_id: str) -> LeaveAuditResult | None:
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM leave_audit_result WHERE request_id = %s", (request_id,))
            row = cur.fetchone()
        if not row:
            return None
        return LeaveAuditResult(
            request_id=row["request_id"],
            status=LeaveAuditStatus(row["status"]),
            plugin_name=row["plugin_name"],
            analysis_json=row["analysis_json"] or {},
            verification_json=row["verification_json"] or {},
            error_message=row["error_message"],
            synced=bool(row["synced"]),
            created_at=_iso(row["created_at"]),
            updated_at=_iso(row["updated_at"]),
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
        decision_status = {
            LeaveAuditStatus.PASS: DecisionStatus.PASS.value,
            LeaveAuditStatus.REVIEW: DecisionStatus.REVIEW_REQUIRED.value,
            LeaveAuditStatus.REJECT: DecisionStatus.REJECT.value,
        }.get(decision.decision)
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO leave_audit_review (request_id, decision, reviewer, comment, created_at) VALUES (%s, %s, %s, %s, %s)",
                (decision.request_id, decision.decision.value, decision.reviewer, decision.comment, decision.created_at),
            )
            cur.execute(
                "UPDATE leave_audit_task SET status = %s, decision_status = COALESCE(%s, decision_status), decision_version = decision_version + 1, updated_at = %s WHERE request_id = %s",
                (decision.decision.value, decision_status, utc_now_iso(), decision.request_id),
            )

    def list_reviews(self, request_id: str) -> list[LeaveReviewDecision]:
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM leave_audit_review WHERE request_id = %s ORDER BY created_at ASC", (request_id,))
            rows = cur.fetchall()
        return [
            LeaveReviewDecision(
                request_id=row["request_id"],
                decision=LeaveAuditStatus(row["decision"]),
                reviewer=row["reviewer"],
                comment=row["comment"],
                created_at=_iso(row["created_at"]),
            )
            for row in rows
        ]

    def stats(self) -> dict[str, int]:
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT status, COUNT(*) AS count FROM leave_audit_task GROUP BY status")
            rows = cur.fetchall()
        return {row["status"]: int(row["count"]) for row in rows}

    def get_field_mappings(self) -> dict[str, list[str]]:
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT canonical_field, candidates_json FROM leave_audit_field_mapping ORDER BY canonical_field")
            rows = cur.fetchall()
        return {row["canonical_field"]: [str(item) for item in (row["candidates_json"] or []) if str(item).strip()] for row in rows}

    def save_field_mapping(self, canonical_field: str, candidates: list[str]) -> None:
        normalized = [str(candidate).strip() for candidate in candidates if str(candidate).strip()]
        if not canonical_field.strip() or not normalized:
            raise ValueError("canonical_field and candidates are required")
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO leave_audit_field_mapping (canonical_field, candidates_json, updated_at)
                VALUES (%s, %s, %s)
                ON CONFLICT(canonical_field) DO UPDATE SET candidates_json=EXCLUDED.candidates_json, updated_at=EXCLUDED.updated_at
                """,
                (canonical_field.strip(), self._json(normalized), utc_now_iso()),
            )

    def get_rule_configs(self) -> list[dict[str, Any]]:
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT leave_type, prompt_text, rules_json, enabled, updated_at FROM leave_audit_rule_config ORDER BY leave_type")
            rows = cur.fetchall()
        return [
            {
                "leave_type": row["leave_type"],
                "prompt_text": row["prompt_text"],
                "rules": row["rules_json"] or [],
                "enabled": bool(row["enabled"]),
                "updated_at": _iso(row["updated_at"]),
            }
            for row in rows
        ]

    def get_rule_config(self, leave_type: str) -> dict[str, Any] | None:
        return next((item for item in self.get_rule_configs() if item["leave_type"] == str(leave_type).upper()), None)

    def save_rule_config(self, leave_type: str, prompt_text: str, rules: list[dict[str, Any]], enabled: bool = True) -> None:
        normalized = str(leave_type).upper().strip()
        if not normalized:
            raise ValueError("leave_type is required")
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO leave_audit_rule_config (leave_type, prompt_text, rules_json, enabled, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT(leave_type) DO UPDATE SET prompt_text=EXCLUDED.prompt_text, rules_json=EXCLUDED.rules_json, enabled=EXCLUDED.enabled, updated_at=EXCLUDED.updated_at
                """,
                (normalized, prompt_text, self._json(rules), enabled, utc_now_iso()),
            )

    def get_prompt_configs(self) -> list[dict[str, Any]]:
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT recognition_type, prompt_type, prompt_text, enabled, updated_at FROM leave_audit_prompt_config ORDER BY recognition_type, prompt_type")
            rows = cur.fetchall()
        return [
            {
                "recognition_type": row["recognition_type"],
                "prompt_type": row["prompt_type"],
                "prompt_text": row["prompt_text"],
                "enabled": bool(row["enabled"]),
                "updated_at": _iso(row["updated_at"]),
            }
            for row in rows
        ]

    def get_effective_prompt_texts(self, recognition_type: str) -> dict[str, str]:
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT recognition_type, prompt_type, prompt_text
                FROM leave_audit_prompt_config
                WHERE enabled = TRUE AND recognition_type IN ('*', %s)
                ORDER BY CASE WHEN recognition_type = '*' THEN 0 ELSE 1 END, prompt_type
                """,
                (str(recognition_type).strip(),),
            )
            rows = cur.fetchall()
        prompts: dict[str, str] = {}
        for row in rows:
            if str(row["prompt_text"] or "").strip():
                prompts[row["prompt_type"]] = row["prompt_text"]
        return prompts

    def save_prompt_config(self, recognition_type: str, prompt_type: str, prompt_text: str, enabled: bool = True) -> None:
        if not str(recognition_type).strip() or not str(prompt_type).strip():
            raise ValueError("recognition_type and prompt_type are required")
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO leave_audit_prompt_config (recognition_type, prompt_type, prompt_text, enabled, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT(recognition_type, prompt_type) DO UPDATE SET prompt_text=EXCLUDED.prompt_text, enabled=EXCLUDED.enabled, updated_at=EXCLUDED.updated_at
                """,
                (str(recognition_type).strip(), str(prompt_type).strip(), prompt_text, enabled, utc_now_iso()),
            )

    def save_config_snapshot(self, snapshot: ConfigSnapshot) -> None:
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO config_version
                (version_id, kind, status, content_json, content_hash, created_by, approved_by, published_at, change_reason, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT(version_id) DO UPDATE SET
                    kind=EXCLUDED.kind, status=EXCLUDED.status, content_json=EXCLUDED.content_json,
                    content_hash=EXCLUDED.content_hash, created_by=EXCLUDED.created_by,
                    approved_by=EXCLUDED.approved_by, published_at=EXCLUDED.published_at,
                    change_reason=EXCLUDED.change_reason
                """,
                (
                    snapshot.version_id,
                    snapshot.kind.value,
                    snapshot.status.value,
                    self._json(snapshot.content),
                    snapshot.content_hash,
                    snapshot.created_by,
                    snapshot.approved_by,
                    snapshot.published_at,
                    snapshot.change_reason,
                    snapshot.created_at,
                ),
            )

    def get_config_snapshot(self, version_id: str) -> ConfigSnapshot | None:
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM config_version WHERE version_id = %s", (version_id,))
            row = cur.fetchone()
        if not row:
            return None
        return ConfigSnapshot(
            version_id=row["version_id"],
            kind=ConfigKind(row["kind"]),
            status=ConfigStatus(row["status"]),
            content=row["content_json"] or {},
            content_hash=row["content_hash"],
            created_by=row["created_by"],
            approved_by=row["approved_by"],
            published_at=_iso(row["published_at"]) if row["published_at"] else None,
            change_reason=row["change_reason"],
            created_at=_iso(row["created_at"]),
        )

    def list_config_snapshots(self, kind: ConfigKind | None = None) -> list[ConfigSnapshot]:
        with self.connect() as conn, conn.cursor() as cur:
            if kind is None:
                cur.execute("SELECT version_id FROM config_version ORDER BY created_at DESC")
            else:
                cur.execute("SELECT version_id FROM config_version WHERE kind = %s ORDER BY created_at DESC", (kind.value,))
            rows = cur.fetchall()
        return [snapshot for row in rows if (snapshot := self.get_config_snapshot(row["version_id"])) is not None]

    def enqueue_outbox_event(self, event: OutboxEvent) -> None:
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO outbox_event
                (event_id, aggregate_type, aggregate_id, event_type, payload, published_at, attempt_count, last_error, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT(event_id) DO NOTHING
                """,
                (
                    event.event_id,
                    event.aggregate_type,
                    event.aggregate_id,
                    event.event_type,
                    self._json(event.payload),
                    event.published_at,
                    event.attempt_count,
                    event.last_error,
                    event.created_at,
                ),
            )

    def list_pending_outbox(self, limit: int = 100) -> list[OutboxEvent]:
        if limit < 1:
            return []
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM outbox_event WHERE published_at IS NULL ORDER BY created_at ASC LIMIT %s",
                (limit,),
            )
            rows = cur.fetchall()
        return [
            OutboxEvent(
                event_id=str(row["event_id"]),
                aggregate_type=row["aggregate_type"],
                aggregate_id=row["aggregate_id"],
                event_type=row["event_type"],
                payload=row["payload"] or {},
                published_at=_iso(row["published_at"]) if row["published_at"] else None,
                attempt_count=int(row["attempt_count"]),
                last_error=row["last_error"],
                created_at=_iso(row["created_at"]),
            )
            for row in rows
        ]

    def mark_outbox_published(self, event_id: str) -> None:
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE outbox_event SET published_at = %s, attempt_count = attempt_count + 1, last_error = NULL WHERE event_id = %s",
                (utc_now_iso(), event_id),
            )

    def mark_outbox_failed(self, event_id: str, error: str) -> None:
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE outbox_event SET attempt_count = attempt_count + 1, last_error = %s WHERE event_id = %s",
                (error, event_id),
            )

    def apply_ocr_result(self, *, consumer_name: str, event_id: str, result: LeaveAuditResult, callback_payload: dict[str, Any] | None = None) -> bool:
        result.updated_at = utc_now_iso()
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute("INSERT INTO consumed_message (consumer_name,event_id,received_at) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING", (consumer_name, event_id, utc_now_iso()))
            if cur.rowcount == 0:
                return False
            cur.execute("""INSERT INTO leave_audit_result (request_id,job_id,attachment_id,status,ocr_status,decision_status,callback_status,decision_version,plugin_name,analysis_json,verification_json,error_message,synced,ocr_profile_snapshot_id,decision_policy_snapshot_id,field_mapping_snapshot_id,callback_policy_snapshot_id,created_at,updated_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT(request_id) DO UPDATE SET job_id=EXCLUDED.job_id,attachment_id=EXCLUDED.attachment_id,status=EXCLUDED.status,ocr_status=EXCLUDED.ocr_status,decision_status=EXCLUDED.decision_status,callback_status=EXCLUDED.callback_status,decision_version=EXCLUDED.decision_version,plugin_name=EXCLUDED.plugin_name,analysis_json=EXCLUDED.analysis_json,verification_json=EXCLUDED.verification_json,error_message=EXCLUDED.error_message,synced=EXCLUDED.synced,updated_at=EXCLUDED.updated_at""",
                (result.request_id,result.job_id,result.attachment_id,result.status.value,result.ocr_status.value,result.decision_status.value if result.decision_status else None,result.callback_status.value,result.decision_version,result.plugin_name,self._json(result.analysis_json),self._json(result.verification_json),result.error_message,result.synced,result.ocr_profile_snapshot_id,result.decision_policy_snapshot_id,result.field_mapping_snapshot_id,result.callback_policy_snapshot_id,result.created_at,result.updated_at))
            cur.execute("UPDATE leave_audit_task SET status=%s,ocr_status=%s,decision_status=%s,callback_status=%s,decision_version=%s,updated_at=%s WHERE request_id=%s", (result.status.value,result.ocr_status.value,result.decision_status.value if result.decision_status else DecisionStatus.PENDING.value,result.callback_status.value,result.decision_version,utc_now_iso(),result.request_id))
            if callback_payload is not None:
                import uuid
                cur.execute("INSERT INTO callback_outbox (callback_id,request_id,decision_version,payload,status,created_at,updated_at) VALUES (%s,%s,%s,%s,'PENDING',%s,%s) ON CONFLICT(request_id,decision_version) DO NOTHING", (str(uuid.uuid4()),result.request_id,result.decision_version,self._json(callback_payload),utc_now_iso(),utc_now_iso()))
            return True

    def list_pending_callbacks(self, limit: int = 100) -> list[CallbackOutboxItem]:
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM callback_outbox WHERE status IN ('PENDING','FAILED') ORDER BY created_at LIMIT %s", (limit,))
            rows = cur.fetchall()
        return [CallbackOutboxItem(callback_id=str(row["callback_id"]), request_id=row["request_id"], decision_version=int(row["decision_version"]), payload=row["payload"] or {}, status=row["status"], attempt_count=int(row["attempt_count"]), next_attempt_at=_iso(row["next_attempt_at"]) if row["next_attempt_at"] else None, last_error=row["last_error"], created_at=_iso(row["created_at"]), updated_at=_iso(row["updated_at"])) for row in rows]

    def mark_callback_processing(self, callback_id: str) -> None:
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute("UPDATE callback_outbox SET status='PROCESSING',attempt_count=attempt_count+1,updated_at=%s WHERE callback_id=%s", (utc_now_iso(),callback_id))

    def mark_callback_succeeded(self, callback_id: str, request_id: str) -> None:
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute("UPDATE callback_outbox SET status='SUCCEEDED',updated_at=%s WHERE callback_id=%s", (utc_now_iso(),callback_id))
            cur.execute("UPDATE leave_audit_task SET callback_status='SUCCEEDED',updated_at=%s WHERE request_id=%s", (utc_now_iso(),request_id))

    def mark_callback_failed(self, callback_id: str, request_id: str, error: str, dead: bool = False) -> None:
        with self.connect() as conn, conn.cursor() as cur:
            state = 'DEAD' if dead else 'FAILED'
            cur.execute("UPDATE callback_outbox SET status=%s,last_error=%s,updated_at=%s WHERE callback_id=%s", (state,error[:500],utc_now_iso(),callback_id))
            cur.execute("UPDATE leave_audit_task SET callback_status=%s,updated_at=%s WHERE request_id=%s", (state,utc_now_iso(),request_id))

    def _row_to_task(self, row: dict[str, Any]) -> LeaveAuditTask:
        attachments = [
            LeaveAttachment(
                attachment_id=str(item.get("attachment_id")),
                attachment_url=str(item.get("attachment_url")),
                filename=item.get("filename"),
                content_type=item.get("content_type"),
                plugin_name=item.get("plugin_name"),
                metadata=dict(item.get("metadata") or {}),
            )
            for item in (row["attachments_json"] or [])
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
            raw_payload=row["raw_payload_json"] or {},
            created_at=_iso(row["created_at"]),
            updated_at=_iso(row["updated_at"]),
            ocr_status=OcrJobStatus(row["ocr_status"]),
            decision_status=DecisionStatus(row["decision_status"]),
            callback_status=CallbackStatus(row["callback_status"]),
            decision_version=int(row["decision_version"]),
            ocr_profile_snapshot_id=row["ocr_profile_snapshot_id"],
            decision_policy_snapshot_id=row["decision_policy_snapshot_id"],
            field_mapping_snapshot_id=row["field_mapping_snapshot_id"],
            callback_policy_snapshot_id=row["callback_policy_snapshot_id"],
        )
