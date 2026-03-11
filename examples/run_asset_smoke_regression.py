import json
from pathlib import Path

from id_doc_ocr.backbones.rapidocr import RapidOCRAdapter


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
    print(json.dumps(results, ensure_ascii=False, indent=2))
