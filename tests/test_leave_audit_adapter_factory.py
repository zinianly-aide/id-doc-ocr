from id_doc_ocr.leave_audit.adapters.factory import create_leave_system_adapter
from id_doc_ocr.leave_audit.adapters.http_leave_system import HttpLeaveSystemAdapter
from id_doc_ocr.leave_audit.adapters.mock_leave_system import MockLeaveSystemAdapter


def test_default_adapter_is_mock(monkeypatch):
    monkeypatch.delenv("ID_DOC_OCR_LEAVE_SYSTEM_ADAPTER", raising=False)

    adapter = create_leave_system_adapter()

    assert isinstance(adapter, MockLeaveSystemAdapter)


def test_env_http_adapter(monkeypatch):
    monkeypatch.setenv("ID_DOC_OCR_LEAVE_SYSTEM_ADAPTER", "http")
    monkeypatch.setenv("ID_DOC_OCR_LEAVE_SYSTEM_BASE_URL", "https://leave.example.test")

    adapter = create_leave_system_adapter()

    assert isinstance(adapter, HttpLeaveSystemAdapter)
    adapter.client.close()
