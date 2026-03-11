import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from id_doc_ocr.backbones.rapidocr import RapidOCRAdapter


REPORT_PATH = Path("reports/asset_smoke_regression_latest.json")


def summarize(results):
    by_category = defaultdict(list)
    for item in results:
        by_category[item["category"]].append(item)
    summary = {}
    for category, items in by_category.items():
        avg_conf = sum(x["confidence"] for x in items) / len(items) if items else 0.0
        avg_lines = sum(x["num_lines"] for x in items) / len(items) if items else 0.0
        summary[category] = {
            "count": len(items),
            "avg_confidence": round(avg_conf, 4),
            "avg_num_lines": round(avg_lines, 2),
            "min_confidence": round(min(x["confidence"] for x in items), 4),
            "max_confidence": round(max(x["confidence"] for x in items), 4),
        }
    return summary


if __name__ == "__main__":
    manifest = json.loads(Path("examples/assets/manifest.json").read_text())
    engine = RapidOCRAdapter()
    results = []
    for sample in manifest["samples"]:
        path = sample["path"]
        result = engine.infer(path)
        results.append({
            "sample_id": sample["sample_id"],
            "category": sample["category"],
            "kind": sample["kind"],
            "num_lines": len(result.get("lines", [])),
            "confidence": result.get("confidence", 0.0),
            "text_preview": result.get("text", "")[:120],
        })
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summarize(results),
        "results": results,
    }
    REPORT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
