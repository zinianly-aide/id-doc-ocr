import json
from pathlib import Path


def test_parser_regression_fixture_exists():
    fixture = Path("examples/fixtures/boarding_pass/public_sample_00006737.expected.json")
    assert fixture.exists()
    payload = json.loads(fixture.read_text())
    assert payload["plugin"] == "boarding_pass"
