import json
from pathlib import Path

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
    assert any(flag["code"] == "weak_perspective_confidence" for flag in payload["result"]["quality"]["flags"])


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
