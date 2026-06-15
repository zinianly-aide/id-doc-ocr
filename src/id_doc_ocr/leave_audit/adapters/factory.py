from __future__ import annotations

import os

from id_doc_ocr.leave_audit.adapters.base import LeaveSystemAdapter
from id_doc_ocr.leave_audit.adapters.mock_leave_system import MockLeaveSystemAdapter


def create_leave_system_adapter(kind: str | None = None) -> LeaveSystemAdapter:
    adapter_kind = (kind or os.getenv("ID_DOC_OCR_LEAVE_SYSTEM_ADAPTER") or "mock").strip().lower()
    if adapter_kind == "mock":
        return MockLeaveSystemAdapter()
    if adapter_kind == "http":
        from id_doc_ocr.leave_audit.adapters.http_leave_system import HttpLeaveSystemAdapter

        return HttpLeaveSystemAdapter()
    if adapter_kind in {"oracle_tna", "oracle-tna"}:
        from id_doc_ocr.leave_audit.adapters.oracle_tna import OracleTNALeaveSystemAdapter

        return OracleTNALeaveSystemAdapter()
    raise ValueError("ID_DOC_OCR_LEAVE_SYSTEM_ADAPTER must be one of: mock, http, oracle_tna")
