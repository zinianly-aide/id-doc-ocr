import builtins
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from id_doc_ocr.service.app import ServiceSettings, create_app


def build_client(tmp_path: Path | None = None, **overrides) -> TestClient:
    defaults = {
        "default_ocr_backend": "mock",
        "default_vlm_backend": "mock",
        "default_detector_backend": "mock",
        "default_rectify_backend": "mock",
    }
    defaults.update(overrides)
    settings = ServiceSettings(default_failure_dir=str(tmp_path) if tmp_path else None, **defaults)
    return TestClient(create_app(settings))


def test_health_exposes_runtime_and_capability_summary():
    client = build_client(
        default_ocr_backend="paddleocr",
        default_vlm_backend="mock",
        default_detector_backend="pil",
        default_rectify_backend="pil",
    )
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["status"] == "ok"
    assert payload["service"] == "id-doc-ocr"
    assert payload["version"] == "0.1.0"
    assert payload["service_info"]["service_name"] == "id-doc-ocr"
    assert payload["default_ocr_backend"] == "paddleocr"
    assert payload["default_vlm_backend"] == "mock"
    assert payload["default_detector_backend"] == "pil"
    assert payload["default_rectify_backend"] == "pil"
    assert payload["summary"]["plugin_count"] >= 1
    assert payload["summary"]["backbones"]["ocr"]["total"] >= 1
    assert payload["summary"]["detectors"]["detector"]["total"] >= 1
    assert payload["summary"]["rectify"]["rectify"]["total"] >= 1
    assert payload["availability"]["plugins"]["total"] == payload["summary"]["plugin_count"]
    assert payload["runtime"]["python"]["version"]
    assert payload["runtime"]["platform"]["system"]
    assert "boarding_pass" in payload["plugins"]
    assert payload["plugin_names"] == payload["plugins"]
    assert any(backbone["name"] == "rapidocr" for backbone in payload["backbones"]["ocr"])
    assert any(item["name"] == "mock_detector" for item in payload["detectors"]["detector"])
    assert any(item["name"] == "PillowRectifyPipeline" for item in payload["rectify"]["rectify"])


def test_capabilities_exposes_plugins_backbones_runtime_and_availability():
    client = build_client(
        default_ocr_backend="paddleocr",
        default_vlm_backend="mock",
        default_detector_backend="pil",
        default_rectify_backend="pil",
    )
    response = client.get("/capabilities")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["service"]["service_name"] == "id-doc-ocr"
    assert payload["service"]["default_ocr_backend"] == "paddleocr"
    assert payload["service"]["default_vlm_backend"] == "mock"
    assert payload["summary"]["plugin_count"] == len(payload["plugins"])
    assert payload["availability"]["plugins"]["total"] == len(payload["plugins"])
    assert payload["runtime"]["python"]["implementation"]
    assert any(plugin["name"] == "boarding_pass" and "maturity" in plugin and "trial_profile" in plugin for plugin in payload["plugins"])
    assert any(backbone["name"] == "rapidocr" and "available" in backbone for backbone in payload["backbones"]["ocr"])
    assert any(backbone["name"] == "paddleocr_vl" and "availability" in backbone for backbone in payload["backbones"]["vlm"])
    assert any(detector["name"] == "mock_detector" and "availability" in detector for detector in payload["detectors"]["detector"])
    assert any(rectify["name"] == "PillowRectifyPipeline" and "availability" in rectify for rectify in payload["rectify"]["rectify"])


def test_capabilities_does_not_import_paddleocr(monkeypatch):
    monkeypatch.setattr("id_doc_ocr.backbones.paddleocr.module_available", lambda name: True)
    monkeypatch.setattr("id_doc_ocr.backbones.paddleocr.package_version", lambda name: "fake-3.0")

    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "paddleocr":
            raise AssertionError("/capabilities should not import paddleocr")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    client = build_client()
    response = client.get("/capabilities")

    assert response.status_code == 200
    payload = response.json()
    paddle = next(
        backbone
        for backbone in payload["backbones"]["ocr"]
        if backbone["name"] == "paddleocr" and backbone["description"] == "PaddleOCR backbone adapter"
    )
    assert paddle["available"] is True
    assert paddle["availability"]["probe"] == "module_spec"


def test_capabilities_does_not_initialize_paddleocr_vl(monkeypatch):
    def guarded_init(self, *args, **kwargs):
        raise AssertionError("/capabilities should not initialize paddleocr_vl")

    monkeypatch.setattr("id_doc_ocr.backbones.paddleocr_vl.PaddleOCRVLAdapter.__init__", guarded_init)

    client = build_client()
    response = client.get("/capabilities")

    assert response.status_code == 200
    payload = response.json()
    assert "detector" in payload["detectors"]
    assert "rectify" in payload["rectify"]


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



def test_verify_attachment_success():
    client = build_client()
    response = client.post(
        "/verify-attachment",
        data={
            "plugin_name": "diagnosis_proof",
            "ocr_backend": "mock",
            "vlm_backend": "mock",
            "expected_attachment_type": "MEDICAL_CERTIFICATE",
            "applicant_name": "张三",
            "leave_start_date": "2026-04-01",
            "leave_end_date": "2026-04-03",
            "patient_name": "张三",
            "rest_start_date": "2026-04-01",
            "rest_end_date": "2026-04-03",
            "issue_date": "2026-04-01",
        },
        files={"file": ("sample.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["request_id"].startswith("LV-TEMP-")
    assert response.headers["x-request-id"] == payload["request_id"]
    assert payload["verification"]["verify_status"] == "PASS"
    assert payload["verification"]["matched_attachment_type"] == "MEDICAL_CERTIFICATE"
    assert payload["analysis"]["classification_evidence"]["attachment_label"] == "MEDICAL_CERTIFICATE"
    assert payload["result"]["analysis"] == payload["analysis"]



def test_verify_attachment_rejects_missing_expected_type():
    client = build_client()
    response = client.post(
        "/verify-attachment",
        data={
            "plugin_name": "diagnosis_proof",
            "ocr_backend": "mock",
            "vlm_backend": "mock",
            "applicant_name": "张三",
        },
        files={"file": ("sample.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "expected_attachment_type is required"



def test_verify_attachment_accepts_leave_type_without_explicit_expected_type():
    client = build_client()
    response = client.post(
        "/verify-attachment",
        data={
            "plugin_name": "marriage_certificate",
            "ocr_backend": "mock",
            "vlm_backend": "mock",
            "leave_type": "MARRIAGE",
            "applicant_name": "张三",
            "leave_start_date": "2024-05-20",
            "leave_end_date": "2024-05-20",
            "holder_name": "张三",
            "registration_date": "2024-05-20",
        },
        files={"file": ("sample.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["verification"]["verify_status"] == "PASS"
    assert payload["verification"]["evidence"]["request"]["resolved_expected_attachment_types"] == ["MARRIAGE_CERTIFICATE"]



def test_verify_attachment_accepts_expected_attachment_types_csv_and_relation_fields():
    client = build_client()
    response = client.post(
        "/verify-attachment",
        data={
            "plugin_name": "marriage_certificate",
            "ocr_backend": "mock",
            "vlm_backend": "mock",
            "expected_attachment_types": "BIRTH_CERTIFICATE,MARRIAGE_CERTIFICATE",
            "applicant_name": "张三",
            "related_person_name": "李四",
            "related_person_relation": "spouse",
            "holder_name": "张三",
            "person_a_name": "张三",
            "person_b_name": "李四",
            "registration_date": "2024-05-20",
        },
        files={"file": ("sample.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["verification"]["evidence"]["request"]["resolved_expected_attachment_types"] == ["BIRTH_CERTIFICATE", "MARRIAGE_CERTIFICATE"]
    assert any(rule["rule_code"] == "related_person_match" and rule["passed"] is True for rule in payload["verification"]["rule_results"])



def test_analyze_document_success_returns_analysis_only_payload():
    client = build_client()
    response = client.post(
        "/analyze-document",
        data={
            "plugin_name": "diagnosis_proof",
            "ocr_backend": "mock",
            "vlm_backend": "mock",
            "patient_name": "张三",
            "rest_start_date": "2026-04-01",
            "rest_end_date": "2026-04-03",
            "issue_date": "2026-04-01",
        },
        files={"file": ("sample.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["request_id"].startswith("LV-TEMP-")
    assert response.headers["x-request-id"] == payload["request_id"]
    assert payload["analysis"]["doc_type"] == "diagnosis_proof"
    assert payload["result"]["analysis"] == payload["analysis"]
    assert "verification" not in payload


def test_request_id_can_be_supplied_by_caller_and_reused_across_analyze_and_verify(caplog: pytest.LogCaptureFixture):
    caplog.set_level("INFO", logger="id_doc_ocr.service.app")
    client = build_client()
    request_id = "LV-SICK-20260429-000123"

    analyze_response = client.post(
        "/analyze-document",
        data={
            "request_id": request_id,
            "plugin_name": "diagnosis_proof",
            "ocr_backend": "mock",
            "vlm_backend": "mock",
            "patient_name": "张三",
            "rest_start_date": "2026-04-01",
            "rest_end_date": "2026-04-03",
            "issue_date": "2026-04-01",
        },
        files={"file": ("sample.jpg", b"fake-image-bytes", "image/jpeg")},
    )

    verify_response = client.post(
        "/verify-attachment",
        data={
            "request_id": request_id,
            "plugin_name": "diagnosis_proof",
            "ocr_backend": "mock",
            "vlm_backend": "mock",
            "leave_type": "SICK",
            "applicant_name": "张三",
            "leave_start_date": "2026-04-01",
            "leave_end_date": "2026-04-03",
            "patient_name": "张三",
            "rest_start_date": "2026-04-01",
            "rest_end_date": "2026-04-03",
            "issue_date": "2026-04-01",
        },
        files={"file": ("sample.jpg", b"fake-image-bytes", "image/jpeg")},
    )

    assert analyze_response.status_code == 200
    assert verify_response.status_code == 200
    assert analyze_response.json()["request_id"] == request_id
    assert verify_response.json()["request_id"] == request_id
    assert analyze_response.headers["x-request-id"] == request_id
    assert verify_response.headers["x-request-id"] == request_id
    log_text = "\n".join(record.getMessage() for record in caplog.records)
    assert f"request_id={request_id}" in log_text
    assert "analyze_input" in log_text
    assert "analyze_result" in log_text
    assert "verify_input" in log_text
    assert "verify_result" in log_text



def test_analyze_document_rejects_missing_plugin_name():
    client = build_client()
    response = client.post(
        "/analyze-document",
        data={"ocr_backend": "mock", "vlm_backend": "mock"},
        files={"file": ("sample.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "plugin_name is required"



def test_infer_uses_service_default_backends_when_request_omits_them():
    client = build_client(
        default_ocr_backend="mock",
        default_vlm_backend="mock",
        default_detector_backend="mock",
        default_rectify_backend="mock",
    )
    response = client.post(
        "/infer",
        data={"plugin_name": "boarding_pass"},
        files={"file": ("sample.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert response.status_code == 200
    payload = response.json()["result"]
    assert payload["ocr_backend"] == "mock"
    assert payload["detector_backend"] == "mock"
    assert payload["rectify_backend"] == "mock"


def test_infer_uses_configured_detector_and_rectify_backends(monkeypatch):
    monkeypatch.setattr("id_doc_ocr.pipeline.runner.PillowDocumentDetectorAdapter.is_available", classmethod(lambda cls: True))
    monkeypatch.setattr("id_doc_ocr.pipeline.runner.PillowRectifyPipeline.is_available", classmethod(lambda cls: True))
    client = build_client()
    response = client.post(
        "/infer",
        data={
            "plugin_name": "boarding_pass",
            "ocr_backend": "mock",
            "vlm_backend": "mock",
            "detector_backend": "pil",
            "rectify_backend": "pil",
        },
        files={"file": ("sample.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert response.status_code == 200
    payload = response.json()["result"]
    assert payload["detector_backend"] == "pil"
    assert payload["rectify_backend"] == "pil"


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
    assert payload["backend"] == {"ocr": "mock", "vlm": "paddleocr_vl", "detector": "mock", "rectify": "mock"}
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
        ("detector_backend", "missing_detector", "Unknown detector backend: missing_detector. Supported values: mock, pil"),
        ("rectify_backend", "missing_rectify", "Unknown rectify backend: missing_rectify. Supported values: mock, pil"),
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


def test_infer_accepts_paddleocr_after_capabilities_probe(monkeypatch):
    class FakePaddleOCR:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def ocr(self, image, cls=True):
            return [[[ [0, 0], [10, 0], [10, 10], [0, 10] ], ("姓名 张三", 0.99)]]

    import types
    import sys

    module = types.ModuleType("paddleocr")
    module.__version__ = "fake-3.0"
    module.PaddleOCR = FakePaddleOCR
    monkeypatch.setitem(sys.modules, "paddleocr", module)
    monkeypatch.setattr("id_doc_ocr.backbones.paddleocr.module_available", lambda name: True)
    monkeypatch.setattr("id_doc_ocr.backbones.paddleocr.package_version", lambda name: "fake-3.0")

    client = build_client()

    capabilities = client.get("/capabilities")
    assert capabilities.status_code == 200

    response = client.post(
        "/infer",
        data={"plugin_name": "boarding_pass", "ocr_backend": "paddleocr", "vlm_backend": "mock"},
        files={"file": ("sample.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.json()["result"]["ocr_backend"] == "paddleocr"
    assert response.json()["result"]["ocr"]["engine"] == "paddleocr"


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


def test_infer_rejects_unavailable_detector_backend(monkeypatch):
    monkeypatch.setattr("id_doc_ocr.pipeline.runner.PillowDocumentDetectorAdapter.is_available", classmethod(lambda cls: False))
    client = build_client()
    response = client.post(
        "/infer",
        data={"plugin_name": "boarding_pass", "ocr_backend": "mock", "vlm_backend": "mock", "detector_backend": "pil"},
        files={"file": ("sample.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Detector backend 'pil' is unavailable. Install Pillow to enable image-aware document localization."


def test_infer_rejects_unavailable_rectify_backend(monkeypatch):
    monkeypatch.setattr("id_doc_ocr.pipeline.runner.PillowRectifyPipeline.is_available", classmethod(lambda cls: False))
    client = build_client()
    response = client.post(
        "/infer",
        data={"plugin_name": "boarding_pass", "ocr_backend": "mock", "vlm_backend": "mock", "rectify_backend": "pil"},
        files={"file": ("sample.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Rectify backend 'pil' is unavailable. Install Pillow to enable image-aware rectify and quality scoring."
