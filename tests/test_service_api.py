from pathlib import Path

from fastapi.testclient import TestClient

from id_doc_ocr.service.app import ServiceSettings, create_app


def build_client(tmp_path: Path | None = None) -> TestClient:
    settings = ServiceSettings(default_failure_dir=str(tmp_path) if tmp_path else None)
    return TestClient(create_app(settings))


def test_health():
    client = build_client()
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["service"] == "id-doc-ocr"
    assert payload["version"] == "0.1.0"
    assert "boarding_pass" in payload["plugins"]


def test_capabilities_exposes_plugins_and_backbones():
    client = build_client()
    response = client.get("/capabilities")
    assert response.status_code == 200
    payload = response.json()
    assert payload["service"]["service_name"] == "id-doc-ocr"
    assert any(plugin["name"] == "boarding_pass" for plugin in payload["plugins"])
    assert any(backbone["name"] == "rapidocr" for backbone in payload["backbones"]["ocr"])
    assert any(backbone["name"] == "paddleocr_vl" for backbone in payload["backbones"]["vlm"])


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
    failure_log = tmp_path / "in_memory_sample.json"
    assert failure_log.exists()


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
