import json
from pathlib import Path

from id_doc_ocr.tools.backbone_benchmark import BackendSpec, load_manifest, render_markdown_report, run_benchmark


def test_backbone_benchmark_runs_on_seed_manifest_with_mock_backend():
    manifest = load_manifest(Path("examples/backbone_benchmark_manifest.json"))
    report = run_benchmark(manifest, [BackendSpec("mock", "mock")])

    assert report["report_name"] == "backbone_benchmark"
    assert report["summary"]["totals"]["num_errors"] == 0
    assert report["summary"]["by_backend"]["ocr=mock,vlm=mock"]["num_cases"] == len(manifest["cases"])
    assert any(item["track"] == "live_image" for item in report["results"])
    assert any(item["track"] == "synthetic_control" for item in report["results"])

    markdown = render_markdown_report(report)
    assert "# Backbone benchmark report" in markdown
    assert "ocr=mock,vlm=mock" in markdown

    json.dumps(report, ensure_ascii=False)
