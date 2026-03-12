import json
from pathlib import Path

FIXTURES = [
    Path("examples/fixtures/boarding_pass/public_sample_00006737.expected.json"),
    Path("examples/fixtures/china_id/basic_front.expected.json"),
    Path("examples/fixtures/china_id/basic_back.expected.json"),
    Path("examples/fixtures/china_id/multiline_address_lowercase_x.expected.json"),
    Path("examples/fixtures/passport/basic_td3_mrz.expected.json"),
    Path("examples/fixtures/passport/text_fallback_unspecified_sex.expected.json"),
    Path("examples/fixtures/hukou_booklet/basic_member_card.expected.json"),
    Path("examples/fixtures/hukou_booklet/standalone_labels_infer_birth.expected.json"),
    Path("examples/fixtures/train_ticket/basic_text_ticket.expected.json"),
    Path("examples/fixtures/train_ticket/name_anchor_priority.expected.json"),
    Path("examples/fixtures/medical_record/basic_outpatient_note.expected.json"),
]



def test_parser_regression_fixtures_have_basic_shape():
    for fixture_path in FIXTURES:
        payload = json.loads(fixture_path.read_text())
        assert payload["plugin"]
        assert payload["expected_fields"]
        assert payload.get("sample") or payload.get("ocr_result")
