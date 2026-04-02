from id_doc_ocr.pipeline.runner import DemoPipelineRunner


def test_runner_annotation_from_mock_ocr():
    runner = DemoPipelineRunner()
    result = runner.run("train_ticket", b"demo", fields={})
    assert result["plugin"] == "train_ticket"
    assert result["detector"]["primary"]["doc_type"] == "train_ticket"
    assert result["annotation"]["doc_type"] == "train_ticket"
    assert isinstance(result["annotation"]["regions"], list)


def test_runner_emits_review_ready_decision_warning_and_evidence():
    runner = DemoPipelineRunner()

    result = runner.run(
        "train_ticket",
        b"demo",
        fields={"ticket_number": "G123456789", "departure_station": "Shanghai"},
    )

    assert result["decision"]["action"] == "review"
    assert result["review"]["decision"] == result["decision"]
    assert result["review"]["warnings"] == result["warnings"]
    assert result["review"]["evidence"] == result["evidence"]
    assert any(warning["stage"] == "quality" for warning in result["warnings"])
    assert any(warning["stage"] == "validation" for warning in result["warnings"])
    assert result["evidence"]["summary"]["ocr_line_count"] == len(result["evidence"]["ocr_lines"])
    assert result["evidence"]["summary"]["field_count"] == len(result["evidence"]["fields"])
    assert any(field["field_name"] == "ticket_number" for field in result["evidence"]["fields"])
