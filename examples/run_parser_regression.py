import json
from pathlib import Path

from id_doc_ocr import plugins  # noqa: F401
from id_doc_ocr.pipeline.runner import DemoPipelineRunner

FIXTURES = [
    Path("examples/fixtures/boarding_pass/public_sample_00006737.expected.json"),
]
REPORT_PATH = Path("reports/parser_regression_latest.json")


if __name__ == "__main__":
    runner = DemoPipelineRunner(ocr_backend="rapidocr")
    results = []
    for fixture_path in FIXTURES:
        fixture = json.loads(fixture_path.read_text())
        result = runner.run(fixture["plugin"], Path(fixture["sample"]))
        expected = fixture["expected_fields"]
        parsed = result["parsed_fields"]
        field_results = []
        matched = 0
        for key, expected_value in expected.items():
            pred = parsed.get(key)
            ok = pred == expected_value
            matched += 1 if ok else 0
            field_results.append({
                "field": key,
                "expected": expected_value,
                "predicted": pred,
                "matched": ok,
            })
        total = len(field_results)
        results.append({
            "fixture": str(fixture_path),
            "plugin": fixture["plugin"],
            "field_exact_match_rate": matched / total if total else 0.0,
            "fields": field_results,
        })
    payload = {
        "num_fixtures": len(results),
        "results": results,
        "overall_field_exact_match_rate": sum(x["field_exact_match_rate"] for x in results) / len(results) if results else 0.0,
    }
    REPORT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
