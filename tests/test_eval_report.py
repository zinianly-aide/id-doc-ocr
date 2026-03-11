from id_doc_ocr.eval.report import EvaluationReport, FieldMetric


def test_evaluation_report_model():
    report = EvaluationReport(
        plugin_name="train_ticket",
        overall_exact_match=0.9,
        fields=[FieldMetric(field_name="ticket_number", exact_match=1.0, support=10)],
    )
    assert report.plugin_name == "train_ticket"
    assert report.fields[0].field_name == "ticket_number"
