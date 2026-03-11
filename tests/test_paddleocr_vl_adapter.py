from id_doc_ocr.backbones.mock import MockPaddleOCRVLAdapter
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


def test_demo_runner_auto_vlm_falls_back_to_mock_when_runtime_missing():
    runner = DemoPipelineRunner(vlm_backend="auto")
    if PaddleOCRVLAdapter.is_runtime_available():
        assert runner.vlm.info.name == "paddleocr_vl"
    else:
        assert isinstance(runner.vlm, MockPaddleOCRVLAdapter)
