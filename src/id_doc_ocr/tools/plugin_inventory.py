from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from id_doc_ocr import plugins as _plugins  # noqa: F401
from id_doc_ocr.core.registry import registry


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_ROOT = REPO_ROOT / "examples" / "fixtures"
PARSER_REPORT_PATH = REPO_ROOT / "reports" / "parser_regression_latest.json"


def _load_fixture_stats() -> dict[str, dict[str, Any]]:
    stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "fixture_count": 0,
            "expected_field_count": 0,
            "live_image_fixture_count": 0,
            "fixtures": [],
        }
    )
    if not FIXTURES_ROOT.exists():
        return {}

    for path in sorted(FIXTURES_ROOT.rglob("*.expected.json")):
        payload = json.loads(path.read_text())
        plugin = payload.get("plugin") or path.parent.name
        sample = str(payload.get("sample") or "")
        expected_fields = payload.get("expected_fields") or {}
        is_live_image = sample.startswith("examples/assets/")
        item = stats[plugin]
        item["fixture_count"] += 1
        item["expected_field_count"] += len(expected_fields)
        item["live_image_fixture_count"] += 1 if is_live_image else 0
        item["fixtures"].append(
            {
                "path": str(path.relative_to(REPO_ROOT)),
                "sample": sample,
                "expected_field_count": len(expected_fields),
                "uses_live_image": is_live_image,
            }
        )
    return dict(stats)


def _load_parser_regression_stats() -> dict[str, Any]:
    if not PARSER_REPORT_PATH.exists():
        return {"generated_at": None, "plugins": {}}

    report = json.loads(PARSER_REPORT_PATH.read_text())
    plugins: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "fixture_count": 0,
            "passed_fixture_count": 0,
            "failed_fixture_count": 0,
            "field_count": 0,
            "matched_field_count": 0,
            "field_exact_match_rate": None,
            "status": "unknown",
        }
    )
    for item in report.get("results", []):
        plugin = item.get("plugin")
        if not plugin:
            continue
        plugin_stats = plugins[plugin]
        plugin_stats["fixture_count"] += 1
        plugin_stats["passed_fixture_count"] += 1 if item.get("status") == "pass" else 0
        plugin_stats["failed_fixture_count"] += 1 if item.get("status") != "pass" else 0
        plugin_stats["field_count"] += int(item.get("num_fields") or 0)
        plugin_stats["matched_field_count"] += int(item.get("num_matched_fields") or 0)

    for plugin, item in plugins.items():
        field_count = item["field_count"]
        item["field_exact_match_rate"] = (
            round(item["matched_field_count"] / field_count, 4) if field_count else None
        )
        item["status"] = "pass" if item["failed_fixture_count"] == 0 else "fail"

    return {
        "generated_at": report.get("generated_at"),
        "plugins": dict(plugins),
    }


def _recommended_trial_profile(supported_backbones: list[str], *, has_live_image_fixture: bool) -> dict[str, str]:
    if "paddleocr" in supported_backbones:
        ocr_backend = "paddleocr"
    elif "rapidocr" in supported_backbones:
        ocr_backend = "rapidocr"
    else:
        ocr_backend = supported_backbones[0] if supported_backbones else "mock"

    vlm_backend = "mock"
    if not has_live_image_fixture and "paddleocr_vl" in supported_backbones:
        vlm_backend = "auto"

    return {
        "ocr_backend": ocr_backend,
        "vlm_backend": vlm_backend,
        "detector_backend": "pil",
        "rectify_backend": "pil",
    }


def _infer_maturity(*, fixture_count: int, live_image_fixture_count: int, regression_status: str | None, field_exact_match_rate: float | None) -> dict[str, Any]:
    if fixture_count >= 2 and live_image_fixture_count >= 1 and regression_status == "pass" and (field_exact_match_rate or 0.0) >= 0.99:
        return {
            "level": "production_candidate",
            "reason": "Multiple fixtures pass with at least one live-image regression sample.",
        }
    if fixture_count >= 1 and regression_status == "pass" and (field_exact_match_rate or 0.0) >= 0.95:
        return {
            "level": "beta",
            "reason": "Fixture-backed parser regression passes, but live-image or coverage breadth is still limited.",
        }
    return {
        "level": "experimental",
        "reason": "Limited fixture evidence or regression signal; verify manually before operational use.",
    }


def build_plugin_inventory() -> list[dict[str, Any]]:
    fixture_stats = _load_fixture_stats()
    regression = _load_parser_regression_stats()
    inventory: list[dict[str, Any]] = []

    for plugin_name in registry.list_plugins():
        plugin = registry.get(plugin_name)
        plugin_fixture_stats = fixture_stats.get(plugin_name, {})
        plugin_regression = regression.get("plugins", {}).get(plugin_name, {})
        supported_backbones = list(plugin.metadata.supported_backbones)
        live_image_fixture_count = int(plugin_fixture_stats.get("live_image_fixture_count") or 0)
        maturity = _infer_maturity(
            fixture_count=int(plugin_fixture_stats.get("fixture_count") or 0),
            live_image_fixture_count=live_image_fixture_count,
            regression_status=plugin_regression.get("status"),
            field_exact_match_rate=plugin_regression.get("field_exact_match_rate"),
        )
        inventory.append(
            {
                "name": plugin.metadata.name,
                "version": plugin.metadata.version,
                "description": plugin.metadata.description,
                "supported_backbones": supported_backbones,
                "schema": plugin.get_schema_name(),
                "tags": plugin.metadata.tags,
                "maturity": maturity,
                "regression": {
                    "generated_at": regression.get("generated_at"),
                    "fixture_count": int(plugin_fixture_stats.get("fixture_count") or 0),
                    "live_image_fixture_count": live_image_fixture_count,
                    "expected_field_count": int(plugin_fixture_stats.get("expected_field_count") or 0),
                    "status": plugin_regression.get("status"),
                    "field_exact_match_rate": plugin_regression.get("field_exact_match_rate"),
                    "passed_fixture_count": int(plugin_regression.get("passed_fixture_count") or 0),
                    "failed_fixture_count": int(plugin_regression.get("failed_fixture_count") or 0),
                },
                "trial_profile": _recommended_trial_profile(
                    supported_backbones,
                    has_live_image_fixture=live_image_fixture_count > 0,
                ),
            }
        )
    return inventory
