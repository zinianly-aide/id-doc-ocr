import json
from pathlib import Path

from id_doc_ocr.tools.failure_log import write_failure_case


def test_write_failure_case_wraps_payload_with_structured_metadata(tmp_path: Path):
    path = write_failure_case(
        tmp_path,
        {
            "plugin": "passport",
            "schema": "passport.schema",
            "ocr_backend": "mock",
            "vlm_backend": "paddleocr_vl",
            "validation": {
                "accepted": False,
                "score": 0.0,
                "issues": [
                    {"code": "missing_mrz", "severity": "error", "message": "missing mrz"},
                    {"code": "weak_signal", "severity": "warning", "message": "weak signal"},
                ],
            },
            "ok": False,
        },
        "sample1",
        metadata={"source_name": "sample1.jpg"},
    )
    payload = json.loads(path.read_text())
    assert path.exists()
    assert payload["sample_id"] == "sample1"
    assert payload["plugin"] == "passport"
    assert payload["backend"] == {"ocr": "mock", "vlm": "paddleocr_vl", "detector": None, "rectify": None, "field_parser": None}
    assert payload["validation"]["accepted"] is False
    assert payload["validation"]["issue_count"] == 2
    assert payload["validation"]["severity_counts"] == {"error": 1, "warning": 1, "info": 0}
    assert payload["source"] == {"kind": "path", "name": "sample1.jpg"}
    assert payload["result"]["ok"] is False
    assert payload["recorded_at"]


def test_write_failure_case_serializes_bytes(tmp_path: Path):
    path = write_failure_case(tmp_path, {"payload": b"abc", "validation": {"accepted": False, "issues": []}}, "sample2")
    assert '"type": "bytes"' in path.read_text()
    assert '"size": 3' in path.read_text()
