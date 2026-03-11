from id_doc_ocr.pipeline.runner import DemoPipelineRunner


def test_demo_runner_exposes_vlm_backend_name():
    runner = DemoPipelineRunner(ocr_backend="mock", vlm_backend="mock")
    result = runner.run(plugin_name="train_ticket", image=b"demo")
    assert result["vlm_backend"] == "paddleocr_vl"
    assert "vlm" in result
