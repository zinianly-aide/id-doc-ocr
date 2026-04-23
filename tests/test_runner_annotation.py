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


def test_runner_includes_medical_record_sick_note_check_in_review_evidence():
    runner = DemoPipelineRunner()
    result = runner.run(
        "medical_record",
        b"demo",
        fields={
            "patient_name": "张三",
            "visit_date": "2026-03-11",
            "sick_note_check": {
                "is_sick_note_like": True,
                "score": 0.88,
                "confidence": "high",
                "matched_features": ["医院抬头", "病休/病假标题"],
                "missing_features": [],
            },
        },
    )

    assert result["merged_fields"]["sick_note_check"]["is_sick_note_like"] is True
    assert any(field["field_name"] == "sick_note_check" for field in result["evidence"]["fields"])



def test_runner_emits_unified_analysis_contract():
    runner = DemoPipelineRunner()
    result = runner.run(
        "diagnosis_proof",
        b"demo",
        fields={"hospital_name": "华山医院", "diagnosis": "上呼吸道感染", "issue_date": "2026-04-01"},
    )

    analysis = result["analysis"]

    assert analysis["doc_type"] == "diagnosis_proof"
    assert analysis["doc_type_confidence"] == result["detector"]["primary"]["confidence"]
    assert analysis["classification_evidence"]["plugin"] == result["plugin"]
    assert analysis["validation"] == result["validation"]
    assert analysis["review"] == result["review"]
    assert analysis["risk"]["review_action"] == result["decision"]["action"]
    assert analysis["risk"]["score"] == result["decision"]["risk_score"]
    assert analysis["extracted_fields"]
    assert any(field["name"] == "hospital_name" for field in analysis["extracted_fields"])
