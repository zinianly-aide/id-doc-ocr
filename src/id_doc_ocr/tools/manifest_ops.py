from __future__ import annotations

from id_doc_ocr.datasets.manifest import DatasetManifest, DatasetSample


def build_manifest(name: str, samples: list[dict]) -> DatasetManifest:
    return DatasetManifest(
        name=name,
        samples=[DatasetSample(**sample) for sample in samples],
    )


def split_manifest(samples: list[dict], train_ratio: float = 0.8) -> dict:
    n = len(samples)
    pivot = int(n * train_ratio)
    return {
        "train": samples[:pivot],
        "val": samples[pivot:],
    }
