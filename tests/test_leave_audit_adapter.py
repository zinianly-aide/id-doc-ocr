from id_doc_ocr.leave_audit.adapters.mock_leave_system import MockLeaveSystemAdapter


def test_mock_adapter_fetches_pending_leave_tasks():
    adapter = MockLeaveSystemAdapter()
    tasks = adapter.fetch_pending_attachments()

    assert len(tasks) >= 3
    assert tasks[0].request_id.startswith("LV-MOCK-")
    assert tasks[0].attachments
    assert adapter.download_attachment(tasks[0].attachments[0].attachment_url)
