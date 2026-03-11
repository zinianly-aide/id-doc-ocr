import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from id_doc_ocr.backbones.rapidocr import RapidOCRAdapter


REPORT_PATH = Path("reports/asset_smoke_regression_latest.json")
MANIFEST_PATH = Path("examples/assets/manifest.json")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(results):
    by_category = defaultdict(list)
    by_kind = defaultdict(list)
    for item in results:
        by_category[item["category"]].append(item)
        by_kind[item["kind"]].append(item)

    def build_summary(groups):
        summary = {}
        for name, items in groups.items():
            avg_conf = sum(x["confidence"] for x in items) / len(items) if items else 0.0
            avg_lines = sum(x["num_lines"] for x in items) / len(items) if items else 0.0
            summary[name] = {
                "count": len(items),
                "avg_confidence": round(avg_conf, 4),
                "avg_num_lines": round(avg_lines, 2),
                "min_confidence": round(min(x["confidence"] for x in items), 4),
                "max_confidence": round(max(x["confidence"] for x in items), 4),
            }
        return dict(sorted(summary.items()))

    return {
        "by_category": build_summary(by_category),
        "by_kind": build_summary(by_kind),
    }


if __name__ == "__main__":
    manifest = json.loads(MANIFEST_PATH.read_text())
    engine = RapidOCRAdapter()
    results = []
    errors = []

    for sample in manifest["samples"]:
        path = Path(sample["path"])
        if not path.exists():
            errors.append({
                "sample_id": sample["sample_id"],
                "path": sample["path"],
                "error": "missing_file",
            })
            continue

        try:
            result = engine.infer(path)
            results.append({
                "sample_id": sample["sample_id"],
                "category": sample["category"],
                "kind": sample["kind"],
                "path": sample["path"],
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "num_lines": len(result.get("lines", [])),
                "confidence": result.get("confidence", 0.0),
                "text_preview": result.get("text", "")[:120],
                "status": "ok",
            })
        except Exception as exc:  # pragma: no cover
            errors.append({
                "sample_id": sample["sample_id"],
                "path": sample["path"],
                "error": str(exc),
            })

    payload = {
        "schema_version": "0.2.0",
        "report_name": "asset_smoke_regression",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runner": {
            "ocr_backend": "rapidocr",
            "manifest_path": str(MANIFEST_PATH),
        },
        "manifest": {
            "name": manifest["name"],
            "version": manifest["version"],
            "source": manifest.get("source"),
            "num_samples": len(manifest["samples"]),
        },
        "totals": {
            "num_samples": len(manifest["samples"]),
            "num_processed": len(results),
            "num_errors": len(errors),
            "status": "pass" if not errors else "fail",
        },
        "summary": summarize(results),
        "errors": errors,
        "results": results,
    }
    REPORT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
