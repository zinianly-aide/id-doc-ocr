import json
from datetime import datetime, timezone
from pathlib import Path

from id_doc_ocr import plugins  # noqa: F401
from id_doc_ocr.core.registry import registry
from id_doc_ocr.pipeline.runner import DemoPipelineRunner

FIXTURES = [
    Path("examples/fixtures/boarding_pass/public_sample_00006737.expected.json"),
    Path("examples/fixtures/train_ticket/basic_text_ticket.expected.json"),
    Path("examples/fixtures/medical_record/basic_outpatient_note.expected.json"),
]
REPORT_PATH = Path("reports/parser_regression_latest.json")


if __name__ == "__main__":
    runner = DemoPipelineRunner(ocr_backend="rapidocr")
    results = []
    total_fields = 0
    matched_fields = 0

    for fixture_path in FIXTURES:
        fixture = json.loads(fixture_path.read_text())
        if fixture.get("ocr_result"):
            plugin = registry.get(fixture["plugin"])
            parsed = runner.parse_plugin_fields(plugin, fixture["ocr_result"])
            sample = fixture.get("sample", "<inline_ocr_result>")
        else:
            result = runner.run(fixture["plugin"], Path(fixture["sample"]))
            parsed = result["parsed_fields"]
            sample = fixture["sample"]

        expected = fixture["expected_fields"]
        field_results = []
        fixture_matched = 0

        for key, expected_value in expected.items():
            pred = parsed.get(key)
            ok = pred == expected_value
            fixture_matched += 1 if ok else 0
            matched_fields += 1 if ok else 0
            total_fields += 1
            field_results.append({
                "field": key,
                "expected": expected_value,
                "predicted": pred,
                "matched": ok,
            })

        total = len(field_results)
        fixture_rate = fixture_matched / total if total else 0.0
        results.append({
            "fixture": str(fixture_path),
            "sample": sample,
            "plugin": fixture["plugin"],
            "status": "pass" if fixture_rate == 1.0 else "fail",
            "num_fields": total,
            "num_matched_fields": fixture_matched,
            "field_exact_match_rate": fixture_rate,
            "fields": field_results,
        })

    payload = {
        "schema_version": "0.2.0",
        "report_name": "parser_regression",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runner": {
            "pipeline": "DemoPipelineRunner",
            "ocr_backend": "rapidocr",
        },
        "totals": {
            "num_fixtures": len(results),
            "num_passed": sum(1 for item in results if item["status"] == "pass"),
            "num_failed": sum(1 for item in results if item["status"] == "fail"),
            "num_fields": total_fields,
            "num_matched_fields": matched_fields,
            "overall_field_exact_match_rate": matched_fields / total_fields if total_fields else 0.0,
            "status": "pass" if all(item["status"] == "pass" for item in results) else "fail",
        },
        "results": results,
    }
    REPORT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
