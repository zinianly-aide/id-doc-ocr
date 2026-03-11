import json
from pathlib import Path


def test_asset_smoke_report_has_manifest_and_totals():
    report = json.loads(Path("reports/asset_smoke_regression_latest.json").read_text())
    assert report["schema_version"] == "0.2.0"
    assert report["report_name"] == "asset_smoke_regression"
    assert report["manifest"]["num_samples"] == report["totals"]["num_samples"]
    assert report["totals"]["num_processed"] + report["totals"]["num_errors"] == report["totals"]["num_samples"]
    assert report["totals"]["status"] in {"pass", "fail"}
    assert "by_category" in report["summary"]
    assert "by_kind" in report["summary"]
    if report["results"]:
        sample = report["results"][0]
        assert len(sample["sha256"]) == 64
        assert sample["size_bytes"] > 0
        assert sample["status"] == "ok"
