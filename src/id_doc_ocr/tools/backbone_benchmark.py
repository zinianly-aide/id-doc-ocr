from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from id_doc_ocr import plugins as _plugins  # noqa: F401
from id_doc_ocr.core.registry import registry
from id_doc_ocr.pipeline.runner import DemoPipelineRunner


@dataclass(frozen=True)
class BackendSpec:
    ocr_backend: str
    vlm_backend: str = "mock"

    @property
    def label(self) -> str:
        return f"ocr={self.ocr_backend},vlm={self.vlm_backend}"


DEFAULT_BACKENDS = [
    BackendSpec("mock", "mock"),
    BackendSpec("rapidocr", "mock"),
    BackendSpec("paddleocr", "mock"),
]


def load_manifest(path: str | Path) -> dict[str, Any]:
    manifest = json.loads(Path(path).read_text())
    manifest.setdefault("schema_version", "0.1.0")
    manifest.setdefault("cases", [])
    return manifest


def run_benchmark(manifest: dict[str, Any], backends: list[BackendSpec]) -> dict[str, Any]:
    case_results: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for backend in backends:
        runner = DemoPipelineRunner(ocr_backend=backend.ocr_backend, vlm_backend=backend.vlm_backend)
        for case in manifest.get("cases", []):
            try:
                result = _run_case(runner, backend, case)
                case_results.append(result)
            except Exception as exc:  # pragma: no cover
                errors.append(
                    {
                        "backend": backend.label,
                        "case_id": case.get("case_id"),
                        "plugin": case.get("plugin"),
                        "error": str(exc),
                    }
                )

    summary = summarize_results(case_results, errors)
    return {
        "schema_version": "0.1.0",
        "report_name": "backbone_benchmark",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest": {
            "name": manifest.get("name"),
            "version": manifest.get("version"),
            "description": manifest.get("description"),
            "num_cases": len(manifest.get("cases", [])),
        },
        "backends": [backend.__dict__ | {"label": backend.label} for backend in backends],
        "summary": summary,
        "results": case_results,
        "errors": errors,
    }


def _run_case(runner: DemoPipelineRunner, backend: BackendSpec, case: dict[str, Any]) -> dict[str, Any]:
    payload = case.get("ocr_result")
    sample = case.get("sample")
    if payload:
        plugin = registry.get(case["plugin"])
        detection = runner.detector.detect(b"", preferred_doc_type=case["plugin"])
        rectify_result = runner.rectify.process(b"", detection=detection.primary)
        parsed_fields = runner.parse_plugin_fields(plugin, payload)
        merged_fields = {**parsed_fields, **(case.get("provided_fields") or {})}
        validation = plugin.validate_fields(merged_fields)
        quality_summary = rectify_result.quality_summary.model_dump()
        review_ready = runner.build_review_ready_payload(
            parsed_fields=parsed_fields,
            merged_fields=merged_fields,
            annotation=runner.to_internal_annotation(case["plugin"], b"", payload, sample_id=case["case_id"]),
            validation=validation,
            quality_summary=quality_summary,
        )
        result = {
            "ocr": payload,
            "parsed_fields": parsed_fields,
            "merged_fields": merged_fields,
            "validation": validation,
            "warnings": [warning.model_dump() for warning in review_ready.warnings],
            "decision": review_ready.decision.model_dump(),
            "evidence": review_ready.evidence.model_dump(),
            "review": review_ready.model_dump(),
            "sample_id": case["case_id"],
            "quality": {"summary": quality_summary},
        }
        input_mode = "ocr_result"
    else:
        result = runner.run(
            case["plugin"],
            Path(sample),
            fields=case.get("provided_fields"),
            sample_id=case["case_id"],
            source_name=sample,
            source_kind="path",
        )
        input_mode = "image"

    expected_fields = case.get("expected_fields") or {}
    field_hits = []
    hit_count = 0
    for field_name, expected_value in expected_fields.items():
        actual_value = result.get("merged_fields", {}).get(field_name)
        matched = actual_value == expected_value
        field_hits.append(
            {
                "field": field_name,
                "expected": expected_value,
                "actual": actual_value,
                "matched": matched,
            }
        )
        hit_count += 1 if matched else 0

    validation = result.get("validation") or {}
    warnings = result.get("warnings") or []
    decision = result.get("decision") or {}
    return {
        "backend": backend.label,
        "ocr_backend": backend.ocr_backend,
        "vlm_backend": backend.vlm_backend,
        "case_id": case["case_id"],
        "case_name": case.get("case_name", case["case_id"]),
        "plugin": case["plugin"],
        "track": case.get("track", "default"),
        "input_mode": input_mode,
        "sample": sample,
        "success": bool(result.get("ocr") is not None),
        "validator_accepted": bool(validation.get("accepted", False)),
        "warning_count": len(warnings),
        "validator_issue_count": len(validation.get("issues") or []),
        "decision": decision.get("action"),
        "decision_reason_codes": decision.get("reason_codes") or [],
        "key_field_total": len(expected_fields),
        "key_field_hits": hit_count,
        "key_field_hit_rate": (hit_count / len(expected_fields)) if expected_fields else None,
        "field_hits": field_hits,
        "parsed_fields": result.get("merged_fields") or {},
        "quality_summary": (result.get("quality") or {}).get("summary") or {},
    }


def summarize_results(results: list[dict[str, Any]], errors: list[dict[str, Any]]) -> dict[str, Any]:
    by_backend: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_track_backend: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in results:
        by_backend[item["backend"]].append(item)
        by_track_backend[(item["track"], item["backend"])].append(item)

    backend_summary = {label: _aggregate(items, errors_for_backend=[e for e in errors if e["backend"] == label]) for label, items in sorted(by_backend.items())}
    track_summary: dict[str, dict[str, Any]] = {}
    for (track, backend), items in sorted(by_track_backend.items()):
        track_summary.setdefault(track, {})[backend] = _aggregate(items, errors_for_backend=[e for e in errors if e["backend"] == backend])

    return {
        "totals": {
            "num_results": len(results),
            "num_errors": len(errors),
            "status": "pass" if not errors else "fail",
        },
        "by_backend": backend_summary,
        "by_track": track_summary,
    }


def _aggregate(items: list[dict[str, Any]], *, errors_for_backend: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(items)
    decision_counts = Counter(item.get("decision") or "unknown" for item in items)
    hit_den = sum(item["key_field_total"] for item in items)
    hit_num = sum(item["key_field_hits"] for item in items)
    return {
        "num_cases": total,
        "num_errors": len(errors_for_backend),
        "success_rate": round(sum(1 for item in items if item["success"]) / total, 4) if total else 0.0,
        "validator_accept_rate": round(sum(1 for item in items if item["validator_accepted"]) / total, 4) if total else 0.0,
        "avg_warning_count": round(sum(item["warning_count"] for item in items) / total, 4) if total else 0.0,
        "avg_validator_issue_count": round(sum(item["validator_issue_count"] for item in items) / total, 4) if total else 0.0,
        "key_field_hits": hit_num,
        "key_field_total": hit_den,
        "key_field_hit_rate": round(hit_num / hit_den, 4) if hit_den else None,
        "decision_distribution": dict(sorted(decision_counts.items())),
    }


def render_markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# Backbone benchmark report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- manifest: `{report['manifest'].get('name')}` v`{report['manifest'].get('version')}`",
        f"- cases: `{report['manifest'].get('num_cases')}`",
        "",
        "## Backend summary",
        "",
        "| Backend | Cases | Success | Validator accepted | Avg warnings | Key field hit rate | Decision distribution |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for backend, summary in report["summary"]["by_backend"].items():
        lines.append(
            "| {backend} | {num_cases} | {success_rate:.2%} | {validator_accept_rate:.2%} | {avg_warning_count:.2f} | {key_field_hit_rate} | {decision_distribution} |".format(
                backend=backend,
                num_cases=summary["num_cases"],
                success_rate=summary["success_rate"],
                validator_accept_rate=summary["validator_accept_rate"],
                avg_warning_count=summary["avg_warning_count"],
                key_field_hit_rate=(f"{summary['key_field_hit_rate']:.2%}" if summary["key_field_hit_rate"] is not None else "n/a"),
                decision_distribution=json.dumps(summary["decision_distribution"], ensure_ascii=False),
            )
        )

    lines.extend(["", "## Track summary", ""])
    for track, backends in report["summary"]["by_track"].items():
        lines.extend([f"### {track}", "", "| Backend | Cases | Success | Validator accepted | Avg warnings | Key field hit rate |", "| --- | ---: | ---: | ---: | ---: | ---: |"])
        for backend, summary in backends.items():
            lines.append(
                "| {backend} | {num_cases} | {success_rate:.2%} | {validator_accept_rate:.2%} | {avg_warning_count:.2f} | {key_field_hit_rate} |".format(
                    backend=backend,
                    num_cases=summary["num_cases"],
                    success_rate=summary["success_rate"],
                    validator_accept_rate=summary["validator_accept_rate"],
                    avg_warning_count=summary["avg_warning_count"],
                    key_field_hit_rate=(f"{summary['key_field_hit_rate']:.2%}" if summary["key_field_hit_rate"] is not None else "n/a"),
                )
            )
        lines.append("")

    lines.extend(["## Per-case highlights", ""])
    for item in report["results"]:
        lines.append(
            "- `{backend}` / `{case_id}` ({track}, {input_mode}): decision=`{decision}`, validator_accepted=`{validator_accepted}`, warnings=`{warning_count}`, key_fields=`{key_field_hits}/{key_field_total}`".format(**item)
        )
    if report.get("errors"):
        lines.extend(["", "## Errors", ""])
        for err in report["errors"]:
            lines.append(f"- `{err['backend']}` / `{err['case_id']}`: {err['error']}")
    lines.append("")
    return "\n".join(lines)


def save_report(report: dict[str, Any], json_path: str | Path, markdown_path: str | Path | None = None) -> None:
    json_target = Path(json_path)
    json_target.parent.mkdir(parents=True, exist_ok=True)
    json_target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if markdown_path is not None:
        markdown_target = Path(markdown_path)
        markdown_target.parent.mkdir(parents=True, exist_ok=True)
        markdown_target.write_text(render_markdown_report(report))
