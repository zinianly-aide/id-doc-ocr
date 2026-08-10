from id_doc_ocr.leave_audit.repository.factory import create_leave_audit_repository
from id_doc_ocr.leave_audit.repository.sqlite_repository import SQLiteRepository


def test_repository_factory_defaults_to_sqlite(monkeypatch, tmp_path):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("ID_DOC_OCR_DATABASE_URL", raising=False)
    monkeypatch.setenv("ID_DOC_OCR_LEAVE_AUDIT_DB", str(tmp_path / "audit.db"))
    assert isinstance(create_leave_audit_repository(), SQLiteRepository)
