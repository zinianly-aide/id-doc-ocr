from pathlib import Path

from id_doc_ocr.tools.failure_log import write_failure_case


def test_write_failure_case(tmp_path: Path):
    path = write_failure_case(tmp_path, {"ok": False}, "sample1")
    assert path.exists()
    assert path.read_text().strip().startswith("{")


def test_write_failure_case_serializes_bytes(tmp_path: Path):
    path = write_failure_case(tmp_path, {"payload": b"abc"}, "sample2")
    assert '"type": "bytes"' in path.read_text()
    assert '"size": 3' in path.read_text()
