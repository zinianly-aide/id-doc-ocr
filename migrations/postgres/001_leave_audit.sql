-- Leave Audit Service PostgreSQL schema, version 1.
-- Applied by scripts/migrate_postgres.py. Keep business and callback status
-- separate: a callback failure must never overwrite a PASS decision.

CREATE TABLE IF NOT EXISTS leave_audit_task (
    request_id TEXT PRIMARY KEY,
    leave_type TEXT NOT NULL,
    employee_id TEXT,
    employee_name TEXT NOT NULL,
    leave_start_date TEXT,
    leave_end_date TEXT,
    status TEXT NOT NULL,
    ocr_status TEXT NOT NULL DEFAULT 'CREATED',
    decision_status TEXT NOT NULL DEFAULT 'PENDING',
    callback_status TEXT NOT NULL DEFAULT 'NOT_REQUIRED',
    decision_version INTEGER NOT NULL DEFAULT 0,
    ocr_profile_snapshot_id TEXT,
    decision_policy_snapshot_id TEXT,
    field_mapping_snapshot_id TEXT,
    callback_policy_snapshot_id TEXT,
    attachments_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    raw_payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS leave_audit_result (
    request_id TEXT PRIMARY KEY REFERENCES leave_audit_task(request_id),
    job_id TEXT,
    attachment_id TEXT,
    status TEXT NOT NULL,
    ocr_status TEXT NOT NULL DEFAULT 'SUCCEEDED',
    decision_status TEXT,
    callback_status TEXT NOT NULL DEFAULT 'NOT_REQUIRED',
    decision_version INTEGER NOT NULL DEFAULT 0,
    plugin_name TEXT,
    analysis_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    verification_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_message TEXT,
    synced BOOLEAN NOT NULL DEFAULT FALSE,
    ocr_profile_snapshot_id TEXT,
    decision_policy_snapshot_id TEXT,
    field_mapping_snapshot_id TEXT,
    callback_policy_snapshot_id TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS ocr_job (
    job_id UUID PRIMARY KEY,
    request_id TEXT NOT NULL REFERENCES leave_audit_task(request_id),
    attachment_id TEXT NOT NULL,
    command_id UUID,
    status TEXT NOT NULL,
    attempt INTEGER NOT NULL DEFAULT 1,
    object_key TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ocr_job_request ON ocr_job(request_id, attachment_id);

CREATE TABLE IF NOT EXISTS leave_audit_review (
    id BIGSERIAL PRIMARY KEY,
    request_id TEXT NOT NULL REFERENCES leave_audit_task(request_id),
    decision TEXT NOT NULL,
    reviewer TEXT NOT NULL,
    comment TEXT,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS leave_audit_field_mapping (
    canonical_field TEXT PRIMARY KEY,
    candidates_json JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS leave_audit_rule_config (
    leave_type TEXT PRIMARY KEY,
    prompt_text TEXT NOT NULL DEFAULT '',
    rules_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS leave_audit_prompt_config (
    recognition_type TEXT NOT NULL,
    prompt_type TEXT NOT NULL,
    prompt_text TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (recognition_type, prompt_type)
);

CREATE TABLE IF NOT EXISTS outbox_event (
    event_id UUID PRIMARY KEY,
    aggregate_type TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    published_at TIMESTAMPTZ,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS callback_outbox (
    callback_id UUID PRIMARY KEY,
    request_id TEXT NOT NULL REFERENCES leave_audit_task(request_id),
    decision_version INTEGER NOT NULL,
    payload JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    attempt_count INTEGER NOT NULL DEFAULT 0,
    next_attempt_at TIMESTAMPTZ,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    UNIQUE (request_id, decision_version)
);

CREATE TABLE IF NOT EXISTS consumed_message (
    consumer_name TEXT NOT NULL,
    event_id TEXT NOT NULL,
    received_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (consumer_name, event_id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    request_id TEXT,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS config_version (
    version_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    status TEXT NOT NULL,
    content_json JSONB NOT NULL,
    content_hash TEXT NOT NULL,
    created_by TEXT NOT NULL,
    approved_by TEXT,
    published_at TIMESTAMPTZ,
    change_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_config_version_kind_status
    ON config_version (kind, status, created_at);

CREATE INDEX IF NOT EXISTS idx_leave_audit_task_ocr_status ON leave_audit_task (ocr_status, created_at);
CREATE INDEX IF NOT EXISTS idx_leave_audit_task_decision_status ON leave_audit_task (decision_status, created_at);
CREATE INDEX IF NOT EXISTS idx_leave_audit_task_callback_status ON leave_audit_task (callback_status, created_at);
CREATE INDEX IF NOT EXISTS idx_leave_audit_result_job_id ON leave_audit_result (job_id);
CREATE INDEX IF NOT EXISTS idx_outbox_event_pending ON outbox_event (created_at) WHERE published_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_callback_outbox_pending ON callback_outbox (next_attempt_at) WHERE status = 'PENDING';
