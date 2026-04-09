import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from id_doc_ocr.service.app import ServiceSettings, create_app


def build_client(tmp_path: Path | None = None) -> TestClient:
    settings = ServiceSettings(default_failure_dir=str(tmp_path) if tmp_path else None)
    return TestClient(create_app(settings))


def test_health_exposes_runtime_and_capability_summary():
    client = build_client()
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["status"] == "ok"
    assert payload["service"] == "id-doc-ocr"
    assert payload["version"] == "0.1.0"
    assert payload["service_info"]["service_name"] == "id-doc-ocr"
    assert payload["summary"]["plugin_count"] >= 1
    assert payload["summary"]["backbones"]["ocr"]["total"] >= 1
    assert payload["availability"]["plugins"]["total"] == payload["summary"]["plugin_count"]
    assert payload["runtime"]["python"]["version"]
    assert payload["runtime"]["platform"]["system"]
    assert "boarding_pass" in payload["plugins"]
    assert payload["plugin_names"] == payload["plugins"]
    assert any(backbone["name"] == "rapidocr" for backbone in payload["backbones"]["ocr"])


def test_capabilities_exposes_plugins_backbones_runtime_and_availability():
    client = build_client()
    response = client.get("/capabilities")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["service"]["service_name"] == "id-doc-ocr"
    assert payload["summary"]["plugin_count"] == len(payload["plugins"])
    assert payload["availability"]["plugins"]["total"] == len(payload["plugins"])
    assert payload["runtime"]["python"]["implementation"]
    assert any(plugin["name"] == "boarding_pass" for plugin in payload["plugins"])
    assert any(backbone["name"] == "rapidocr" and "available" in backbone for backbone in payload["backbones"]["ocr"])
    assert any(backbone["name"] == "paddleocr_vl" and "availability" in backbone for backbone in payload["backbones"]["vlm"])


def test_infer_success():
    client = build_client()
    response = client.post(
        "/infer",
        data={"plugin_name": "boarding_pass", "ocr_backend": "mock", "vlm_backend": "mock"},
        files={"file": ("sample.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["filename"] == "sample.jpg"
    assert payload["result"]["plugin"] == "boarding_pass"
    assert payload["result"]["detector"]["primary"]["doc_type"] == "boarding_pass"
    assert payload["result"]["quality"]["summary"]["routing_hint"] == "review"
    assert payload["result"]["decision"]["action"] == "review"
    assert payload["result"]["review"]["decision"] == payload["result"]["decision"]
    assert payload["result"]["review"]["warnings"] == payload["result"]["warnings"]
    assert payload["result"]["review"]["evidence"] == payload["result"]["evidence"]
    assert any(flag["code"] == "weak_perspective_confidence" for flag in payload["result"]["quality"]["flags"])
    assert any(warning["stage"] == "validation" for warning in payload["result"]["warnings"])
    assert payload["result"]["evidence"]["summary"]["validator_issue_count"] >= 1


def test_infer_accepts_plugin_alias_field():
    client = build_client()
    response = client.post(
        "/infer",
        data={"plugin": "boarding_pass", "ocr_backend": "mock", "vlm_backend": "mock"},
        files={"file": ("sample.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.json()["result"]["plugin"] == "boarding_pass"


def test_infer_uses_default_failure_dir_for_invalid_result(tmp_path: Path):
    client = build_client(tmp_path)
    response = client.post(
        "/infer",
        data={"plugin_name": "passport", "ocr_backend": "mock", "vlm_backend": "mock"},
        files={"file": ("sample.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert response.status_code == 200
    failure_log = tmp_path / "sample.json"
    assert failure_log.exists()
    payload = json.loads(failure_log.read_text())
    assert payload["sample_id"] == "sample"
    assert payload["plugin"] == "passport"
    assert payload["backend"] == {"ocr": "mock", "vlm": "paddleocr_vl"}
    assert payload["validation"]["accepted"] is False
    assert payload["source"] == {"kind": "path", "name": "sample.jpg"}
    assert payload["result"]["sample_id"] == "sample"


def test_infer_rejects_missing_plugin_name():
    client = build_client()
    response = client.post(
        "/infer",
        data={},
        files={"file": ("sample.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "plugin_name is required"


def test_infer_rejects_unknown_plugin():
    client = build_client()
    response = client.post(
        "/infer",
        data={"plugin_name": "missing_plugin"},
        files={"file": ("sample.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert response.status_code == 404


def test_infer_rejects_empty_file():
    client = build_client()
    response = client.post(
        "/infer",
        data={"plugin_name": "boarding_pass"},
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 400


def test_infer_returns_422_when_runner_init_raises_runtime_error(monkeypatch):
    class _BoomRunner:
        @staticmethod
        def validate_backend_selection(**kwargs):
            return None

        def __init__(self, *args, **kwargs):
            raise RuntimeError("backend init failed")

    monkeypatch.setattr("id_doc_ocr.service.app.DemoPipelineRunner", _BoomRunner)
    client = build_client()
    response = client.post(
        "/infer",
        data={"plugin_name": "boarding_pass", "ocr_backend": "paddleocr", "vlm_backend": "mock"},
        files={"file": ("sample.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "backend init failed"


@pytest.mark.parametrize(
    ("field", "value", "expected_detail"),
    [
        ("ocr_backend", "missing_ocr", "Unknown OCR backend: missing_ocr. Supported values: mock, paddleocr, rapidocr"),
        ("vlm_backend", "missing_vlm", "Unknown VLM backend: missing_vlm. Supported values: auto, mock, paddleocr_vl"),
    ],
)
def test_infer_rejects_unknown_backend(field: str, value: str, expected_detail: str):
    client = build_client()
    payload = {"plugin_name": "boarding_pass", "ocr_backend": "mock", "vlm_backend": "mock"}
    payload[field] = value
    response = client.post(
        "/infer",
        data=payload,
        files={"file": ("sample.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == expected_detail


def test_infer_rejects_unavailable_paddleocr_backend(monkeypatch):
    monkeypatch.setattr("id_doc_ocr.pipeline.runner.PaddleOCRAdapter.is_available", classmethod(lambda cls: False))
    client = build_client()
    response = client.post(
        "/infer",
        data={"plugin_name": "boarding_pass", "ocr_backend": "paddleocr", "vlm_backend": "mock"},
        files={"file": ("sample.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "OCR backend 'paddleocr' is unavailable. See docs/paddleocr-setup.md for local setup instructions."


@pytest.mark.parametrize("vlm_backend", ["paddleocr_vl", "auto"])
def test_infer_rejects_unavailable_vlm_backend(monkeypatch, vlm_backend: str):
    monkeypatch.setattr("id_doc_ocr.pipeline.runner.PaddleOCRVLAdapter.is_runtime_available", classmethod(lambda cls: False))
    client = build_client()
    response = client.post(
        "/infer",
        data={"plugin_name": "boarding_pass", "ocr_backend": "mock", "vlm_backend": vlm_backend},
        files={"file": ("sample.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == (
        f"VLM backend '{vlm_backend}' is unavailable. Install optional PaddleOCR-VL runtime dependencies first."
    )
