from id_doc_ocr.tools.manifest_ops import build_manifest, split_manifest


def test_build_manifest_and_split():
    samples = [
        {"sample_id": "1", "doc_type": "china_id", "image_path": "a.jpg"},
        {"sample_id": "2", "doc_type": "passport", "image_path": "b.jpg"},
    ]
    manifest = build_manifest("demo", samples)
    assert manifest.name == "demo"
    assert len(manifest.samples) == 2
    split = split_manifest(samples, train_ratio=0.5)
    assert len(split["train"]) == 1
    assert len(split["val"]) == 1
