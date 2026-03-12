from fastapi.testclient import TestClient

from id_doc_ocr.service.app import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert "boarding_pass" in payload["plugins"]


def test_infer_success():
    response = client.post(
        "/infer",
        data={"plugin_name": "boarding_pass", "ocr_backend": "mock", "vlm_backend": "mock"},
        files={"file": ("sample.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["filename"] == "sample.jpg"
    assert payload["result"]["plugin"] == "boarding_pass"


def test_infer_rejects_unknown_plugin():
    response = client.post(
        "/infer",
        data={"plugin_name": "missing_plugin"},
        files={"file": ("sample.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert response.status_code == 404


def test_infer_rejects_empty_file():
    response = client.post(
        "/infer",
        data={"plugin_name": "boarding_pass"},
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 400
