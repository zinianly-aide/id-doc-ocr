import json
from pathlib import Path


def test_asset_manifest_has_multiple_categories_and_metadata():
    manifest = json.loads(Path("examples/assets/manifest.json").read_text())
    categories = {s["category"] for s in manifest["samples"]}
    assert manifest["schema_version"] == "0.2.0"
    assert manifest["num_samples"] == len(manifest["samples"])
    assert len(manifest["samples"]) >= 24
    assert "boarding_pass" in categories
    assert "receipt" in categories
    assert "table" in categories
    assert "layout" in categories
    assert "captcha" in categories
    assert "char_rec" in categories

    sample = manifest["samples"][0]
    assert sample["source_url"].startswith("https://raw.githubusercontent.com/PaddlePaddle/PaddleOCR/main/")
    assert sample["license"] == "Apache-2.0"
    assert len(sample["sha256"]) == 64
    assert sample["size_bytes"] > 0
