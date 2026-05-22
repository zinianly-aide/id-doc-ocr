import os
import subprocess
import sys
from pathlib import Path

from id_doc_ocr.leave_audit.repository.sqlite_repository import SQLiteRepository
from scripts.reset_leave_audit_demo import reset_database


def test_reset_database_recreates_demo_schema(tmp_path):
    db_path = tmp_path / "leave_audit.db"
    repo = SQLiteRepository(db_path)
    with repo.connect() as conn:
        conn.execute("INSERT INTO leave_audit_task (request_id, leave_type, employee_name, status, attachments_json, raw_payload_json, created_at, updated_at) VALUES ('LV-OLD', 'SICK', '张三', 'PULLED', '[]', '{}', 'now', 'now')")

    reset_database(db_path)

    fresh = SQLiteRepository(db_path)
    assert fresh.list_tasks() == []
    assert db_path.exists()
    assert db_path.parent == tmp_path


def test_reset_script_is_executable_with_tmp_db(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    db_path = tmp_path / "demo.db"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")

    result = subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "reset_leave_audit_demo.py"), "--db-path", str(db_path)],
        cwd=repo_root,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )

    assert db_path.exists()
    assert "Reset leave_audit demo database" in result.stdout
    assert "curl -X POST http://127.0.0.1:8000/leave-audit/sync" in result.stdout
