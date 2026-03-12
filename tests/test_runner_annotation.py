from id_doc_ocr.pipeline.runner import DemoPipelineRunner


def test_runner_annotation_from_mock_ocr():
    runner = DemoPipelineRunner()
    result = runner.run("train_ticket", b"demo", fields={})
    assert result["plugin"] == "train_ticket"
    assert result["detector"]["primary"]["doc_type"] == "train_ticket"
    assert result["annotation"]["doc_type"] == "train_ticket"
    assert isinstance(result["annotation"]["regions"], list)
