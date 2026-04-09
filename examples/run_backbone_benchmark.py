from __future__ import annotations

import argparse
import json
from pathlib import Path

from id_doc_ocr.tools.backbone_benchmark import DEFAULT_BACKENDS, BackendSpec, load_manifest, render_markdown_report, run_benchmark, save_report


DEFAULT_MANIFEST = Path("examples/backbone_benchmark_manifest.json")
DEFAULT_JSON_REPORT = Path("reports/backbone_benchmark_latest.json")
DEFAULT_MD_REPORT = Path("reports/backbone_benchmark_latest.md")


def parse_backend_specs(values: list[str] | None) -> list[BackendSpec]:
    if not values:
        return DEFAULT_BACKENDS
    specs: list[BackendSpec] = []
    for value in values:
        ocr_backend, _, vlm_backend = value.partition(":")
        specs.append(BackendSpec(ocr_backend=ocr_backend, vlm_backend=vlm_backend or "mock"))
    return specs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the minimal OCR/VLM backbone benchmark template")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument(
        "--backend",
        action="append",
        help="Backend spec in the form ocr_backend or ocr_backend:vlm_backend. Repeatable. Defaults to mock, rapidocr, paddleocr with vlm=mock.",
    )
    parser.add_argument("--report-json", default=str(DEFAULT_JSON_REPORT))
    parser.add_argument("--report-md", default=str(DEFAULT_MD_REPORT))
    parser.add_argument("--print-markdown", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    manifest = load_manifest(args.manifest)
    backends = parse_backend_specs(args.backend)
    report = run_benchmark(manifest, backends)
    save_report(report, args.report_json, args.report_md)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.print_markdown:
        print("\n--- MARKDOWN REPORT ---\n")
        print(render_markdown_report(report))


if __name__ == "__main__":
    main()
