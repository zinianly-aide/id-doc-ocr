from __future__ import annotations

import builtins
import sys
import types
from pathlib import Path

import pytest

from id_doc_ocr.pipeline.runner import DemoPipelineRunner


def install_fake_paddleocr(monkeypatch, *, result=None):
    class FakePaddleOCR:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def ocr(self, image, cls=True):
            self.image = image
            self.cls = cls
            return result if result is not None else []

    module = types.ModuleType("paddleocr")
    module.__version__ = "fake-1.0"
    module.PaddleOCR = FakePaddleOCR
    monkeypatch.setitem(sys.modules, "paddleocr", module)
    return FakePaddleOCR


def test_paddleocr_adapter_availability_shape(monkeypatch):
    monkeypatch.delitem(sys.modules, "paddleocr", raising=False)

    from id_doc_ocr.backbones.paddleocr import PaddleOCRAdapter

    details = PaddleOCRAdapter.availability_details()
    assert "available" in details
    assert details["package"] == "paddleocr"


def test_paddleocr_adapter_availability_probe_is_lazy(monkeypatch):
    from id_doc_ocr.backbones.paddleocr import PaddleOCRAdapter

    monkeypatch.setattr("id_doc_ocr.backbones.paddleocr.module_available", lambda name: True)
    monkeypatch.setattr("id_doc_ocr.backbones.paddleocr.package_version", lambda name: "fake-3.0")

    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "paddleocr":
            raise AssertionError("availability probe should not import paddleocr")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    details = PaddleOCRAdapter.availability_details()

    assert details["available"] is True
    assert details["version"] == "fake-3.0"
    assert details["probe"] == "module_spec"


def test_paddleocr_adapter_normalizes_result(monkeypatch):
    install_fake_paddleocr(
        monkeypatch,
        result=[[
            [
                [[0, 0], [10, 0], [10, 10], [0, 10]],
                ("姓名 张三", 0.99),
            ],
            [
                [[0, 11], [10, 11], [10, 21], [0, 21]],
                ("证件号 123456", 0.88),
            ],
        ]],
    )

    from id_doc_ocr.backbones.paddleocr import PaddleOCRAdapter

    monkeypatch.setattr("id_doc_ocr.backbones.paddleocr.module_available", lambda name: True)
    monkeypatch.setattr("id_doc_ocr.backbones.paddleocr.package_version", lambda name: "fake-3.0")

    adapter = PaddleOCRAdapter(lang="ch")
    result = adapter.infer(Path("examples/assets/paddle_sample_doc_00006737.jpg"))

    assert result["engine"] == "paddleocr"
    assert result["text"] == "姓名 张三\n证件号 123456"
    assert len(result["lines"]) == 2
    assert result["confidence"] == pytest.approx((0.99 + 0.88) / 2)
    assert result["availability"]["available"] is True
    assert result["config"]["lang"] == "ch"


def test_paddleocr_adapter_skips_empty_text_and_normalizes_dirty_scores(monkeypatch):
    install_fake_paddleocr(
        monkeypatch,
        result=[
            {
                "rec_texts": ["  ", "姓名 李四"],
                "rec_scores": ["nan?", "0.87"],
                "dt_polys": [None, None],
            }
        ],
    )

    from id_doc_ocr.backbones.paddleocr import PaddleOCRAdapter

    adapter = PaddleOCRAdapter(lang="ch")
    result = adapter.infer("dummy.png")

    assert result["text"] == "姓名 李四"
    assert len(result["lines"]) == 1
    assert result["lines"][0]["score"] == pytest.approx(0.87)
    assert result["confidence"] == pytest.approx(0.87)


def test_runner_accepts_paddleocr_backend(monkeypatch):
    install_fake_paddleocr(monkeypatch, result=[])

    runner = DemoPipelineRunner(ocr_backend="paddleocr")

    assert runner.ocr_backend == "paddleocr"
    assert runner.ocr.info.name == "paddleocr"
