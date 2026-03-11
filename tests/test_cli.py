from id_doc_ocr.tools.dataset_quality import summarize_dataset


def test_dataset_summary():
    result = summarize_dataset([
        {"doc_type": "china_id"},
        {"doc_type": "train_ticket"},
        {"doc_type": "china_id"},
    ])
    assert result["num_samples"] == 3
    assert result["doc_types"] == ["china_id", "train_ticket"]
