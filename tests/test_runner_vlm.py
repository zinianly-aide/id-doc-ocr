from id_doc_ocr.pipeline.runner import DemoPipelineRunner


def test_demo_runner_exposes_vlm_backend_name():
    runner = DemoPipelineRunner(ocr_backend="mock", vlm_backend="mock")
    result = runner.run(plugin_name="train_ticket", image=b"demo")
    assert result["vlm_backend"] == "paddleocr_vl"
    assert "vlm" in result


def test_demo_runner_tracks_selected_stage_backends():
    runner = DemoPipelineRunner(ocr_backend="mock", vlm_backend="mock", detector_backend="mock", rectify_backend="mock")

    assert runner.backend_selection == {
        "ocr": "mock",
        "vlm": "mock",
        "detector": "mock",
        "rectify": "mock",
    }


def test_demo_runner_exposes_stage_backend_registry_inventory():
    inventory = DemoPipelineRunner.build_stage_inventory()

    assert DemoPipelineRunner.stage_backend_names("ocr") == ["mock", "paddleocr", "rapidocr"]
    assert DemoPipelineRunner.stage_backend_names("detector") == ["mock", "pil"]
    assert {item["name"] for item in inventory["rectify"]} >= {"MockRectifyPipeline", "PillowRectifyPipeline"}
    assert {item["backend"] for item in inventory["detector"]} == {"mock", "pil"}
    assert {item["backend"] for item in inventory["rectify"]} == {"mock", "pil"}
    assert all("available" in item for stage in inventory.values() for item in stage)
