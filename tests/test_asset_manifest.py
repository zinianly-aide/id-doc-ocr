import json
from pathlib import Path


def test_asset_manifest_has_multiple_categories():
    manifest = json.loads(Path("examples/assets/manifest.json").read_text())
    categories = {s["category"] for s in manifest["samples"]}
    assert len(manifest["samples"]) >= 10
    assert "boarding_pass" in categories
    assert "receipt" in categories
    assert "table" in categories
