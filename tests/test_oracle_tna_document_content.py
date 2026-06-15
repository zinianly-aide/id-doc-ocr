import sqlite3

import pytest

from id_doc_ocr.leave_audit.adapters.factory import create_leave_system_adapter
from id_doc_ocr.leave_audit.adapters.oracle_tna import OracleDocumentContentService, OracleTNALeaveSystemAdapter


def create_doc_db(path):
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE TBCN_DOC_CONTENT (
                DOC_CONTENT_INDEX TEXT PRIMARY KEY,
                MIME_TYPE TEXT NOT NULL,
                DOC_SIZE INTEGER,
                IS_ARCHIVE TEXT,
                CONTENT BLOB NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT INTO TBCN_DOC_CONTENT (DOC_CONTENT_INDEX, MIME_TYPE, DOC_SIZE, IS_ARCHIVE, CONTENT) VALUES (?, ?, ?, ?, ?)",
            ("DOC-IMG-001", "image/jpeg", 4, "N", b"jpeg"),
        )
        conn.execute(
            "INSERT INTO TBCN_DOC_CONTENT (DOC_CONTENT_INDEX, MIME_TYPE, DOC_SIZE, IS_ARCHIVE, CONTENT) VALUES (?, ?, ?, ?, ?)",
            ("DOC-XML-001", "text/xml", 5, "N", b"<xml>"),
        )


def test_oracle_document_content_service_reads_non_xml_binary(tmp_path):
    db_path = tmp_path / "tna.db"
    create_doc_db(db_path)

    service = OracleDocumentContentService(db_path=db_path, table_name="TBCN_DOC_CONTENT")
    content = service.fetch("DOC-IMG-001")

    assert content.doc_content_index == "DOC-IMG-001"
    assert content.mime_type == "image/jpeg"
    assert content.doc_size == 4
    assert content.content == b"jpeg"


def test_oracle_document_content_service_excludes_xml(tmp_path):
    db_path = tmp_path / "tna.db"
    create_doc_db(db_path)

    service = OracleDocumentContentService(db_path=db_path, table_name="TBCN_DOC_CONTENT")
    with pytest.raises(FileNotFoundError):
        service.fetch("DOC-XML-001")


def test_oracle_tna_adapter_downloads_document_content(tmp_path):
    db_path = tmp_path / "tna.db"
    create_doc_db(db_path)
    service = OracleDocumentContentService(db_path=db_path, table_name="TBCN_DOC_CONTENT")
    source = type("Source", (), {"fetch_tasks": lambda self: []})()
    adapter = OracleTNALeaveSystemAdapter(source=source, document_service=service)

    assert adapter.download_attachment("oracle-tna://DOC-IMG-001") == b"jpeg"
    assert adapter.download_attachment("tna-doc://DOC-IMG-001") == b"jpeg"
    assert adapter.download_attachment("DOC_CONTENT_INDEX:DOC-IMG-001") == b"jpeg"


def test_factory_creates_oracle_tna_adapter_with_sqlite_env(tmp_path, monkeypatch):
    tna_db = tmp_path / "tna.db"
    create_doc_db(tna_db)
    with sqlite3.connect(tna_db) as conn:
        conn.execute("CREATE TABLE tna_leave_audit_task (payload_json TEXT NOT NULL)")
    monkeypatch.setenv("ID_DOC_OCR_LEAVE_SYSTEM_ADAPTER", "oracle_tna")
    monkeypatch.setenv("ID_DOC_OCR_ORACLE_TNA_DB", str(tna_db))
    monkeypatch.setenv("ID_DOC_OCR_ORACLE_TNA_DOC_TABLE", "TBCN_DOC_CONTENT")

    adapter = create_leave_system_adapter()

    assert isinstance(adapter, OracleTNALeaveSystemAdapter)
