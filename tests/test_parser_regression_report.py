import json
from pathlib import Path

FIXTURES = {
    "examples/fixtures/boarding_pass/public_sample_00006737.expected.json": "boarding_pass",
    "examples/fixtures/train_ticket/basic_text_ticket.expected.json": "train_ticket",
    "examples/fixtures/medical_record/basic_outpatient_note.expected.json": "medical_record",
}



def test_parser_regression_fixture_exists():
    for path, plugin in FIXTURES.items():
        fixture = Path(path)
        assert fixture.exists()
        payload = json.loads(fixture.read_text())
        assert payload["plugin"] == plugin



def test_parser_regression_report_has_status_totals():
    report = json.loads(Path("reports/parser_regression_latest.json").read_text())
    assert report["schema_version"] == "0.2.0"
    assert report["report_name"] == "parser_regression"
    assert report["totals"]["num_fixtures"] >= 1
    assert report["totals"]["num_fields"] >= report["totals"]["num_matched_fields"]
    assert report["totals"]["status"] in {"pass", "fail"}
    assert all(item["status"] in {"pass", "fail"} for item in report["results"])
