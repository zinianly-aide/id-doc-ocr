from pathlib import Path


def test_rapidocr_adapter_importable():
    from id_doc_ocr.backbones.rapidocr import RapidOCRAdapter

    assert RapidOCRAdapter.info.name == "rapidocr"
    assert Path("examples/assets/paddle_sample_doc_00006737.jpg").exists()


def test_rapidocr_adapter_availability_shape(monkeypatch):
    from id_doc_ocr.backbones.rapidocr import RapidOCRAdapter

    monkeypatch.setattr("id_doc_ocr.backbones.rapidocr.module_available", lambda name: False)
    details = RapidOCRAdapter.availability_details()

    assert details["available"] is False
    assert details["package"] == "rapidocr_onnxruntime"
    assert details["probe"] == "module_spec"
