import pytest

from id_doc_ocr.backbones.paddleocr_vl import PaddleOCRVLAdapter
from id_doc_ocr.pipeline.runner import DemoPipelineRunner


class _FakeEngine:
    def predict(self, image):
        return [
            {"text": "住院病历", "score": 0.99, "bbox": [0, 0, 100, 20], "field": "title", "value": "住院病历"},
            ([0, 20, 100, 40], "姓名 张三", 0.95),
            {"items": [{"key": "patient_name", "value": "张三"}]},
        ]


def test_paddleocr_vl_adapter_runtime_status_shape():
    status = PaddleOCRVLAdapter.runtime_status()
    assert status["engine"] == "paddleocr_vl"
    assert "required_modules" in status


def test_paddleocr_vl_adapter_normalizes_fake_engine_output():
    adapter = PaddleOCRVLAdapter(auto_init=False, engine=_FakeEngine())
    result = adapter.infer("dummy.png")
    assert result["status"] == "ok"
    assert "住院病历" in result["text"]
    assert result["kv"]["patient_name"] == "张三"
    assert result["confidence"] > 0
    assert len(result["layout"]) >= 2


def test_paddleocr_vl_adapter_reports_unavailable_without_runtime():
    adapter = PaddleOCRVLAdapter(auto_init=False)
    result = adapter.infer("dummy.png")
    assert result["status"] == "unavailable"
    assert result["engine"] == "paddleocr_vl"


def test_paddleocr_vl_adapter_dedupes_text_and_normalizes_string_scores():
    class _EngineWithDuplicates:
        def predict(self, image):
            return [
                {"text": "门诊记录", "score": "0.5"},
                {"text": "门诊记录", "score": 0.9},
                ([0, 0, 1, 1], "姓名 王五", "0.8"),
            ]

    adapter = PaddleOCRVLAdapter(auto_init=False, engine=_EngineWithDuplicates())
    result = adapter.infer("dummy.png")

    assert result["text"] == "门诊记录\n姓名 王五"
    assert result["confidence"] == pytest.approx((0.5 + 0.9 + 0.8) / 3)


def test_demo_runner_auto_vlm_uses_requested_backend_without_mock_fallback():
    runner = DemoPipelineRunner(vlm_backend="auto")
    assert runner.vlm.info.name == "paddleocr_vl"
    if not PaddleOCRVLAdapter.is_runtime_available():
        assert runner.vlm.infer("dummy.png")["status"] == "unavailable"
