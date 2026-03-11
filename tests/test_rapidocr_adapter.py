from pathlib import Path


def test_rapidocr_adapter_importable():
    from id_doc_ocr.backbones.rapidocr import RapidOCRAdapter

    assert RapidOCRAdapter.info.name == "rapidocr"
    assert Path("examples/assets/paddle_sample_doc_00006737.jpg").exists()
