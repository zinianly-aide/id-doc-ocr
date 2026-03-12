from id_doc_ocr.cli.main import build_parser
from id_doc_ocr.tools.dataset_quality import summarize_dataset


def test_dataset_summary():
    result = summarize_dataset([
        {"doc_type": "china_id"},
        {"doc_type": "train_ticket"},
        {"doc_type": "china_id"},
    ])
    assert result["num_samples"] == 3
    assert result["doc_types"] == ["china_id", "train_ticket"]


def test_serve_parser_accepts_failure_dir():
    parser = build_parser()
    args = parser.parse_args(["serve", "--failure-dir", "./failures"])
    assert args.command == "serve"
    assert args.failure_dir == "./failures"
