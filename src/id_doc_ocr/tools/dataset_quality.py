def summarize_dataset(samples: list[dict]) -> dict:
    return {
        "num_samples": len(samples),
        "doc_types": sorted({s.get('doc_type', 'unknown') for s in samples}),
    }
