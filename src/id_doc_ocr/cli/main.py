from __future__ import annotations

import argparse
import json

from id_doc_ocr.core.registry import registry
from id_doc_ocr.tools.dataset_quality import summarize_dataset


def cmd_list_plugins(_: argparse.Namespace) -> None:
    print(json.dumps(registry.list_plugins(), ensure_ascii=False, indent=2))


def cmd_validate_plugin(args: argparse.Namespace) -> None:
    plugin = registry.get(args.name)
    print(json.dumps({
        "name": plugin.metadata.name,
        "description": plugin.metadata.description,
        "supported_backbones": plugin.metadata.supported_backbones,
    }, ensure_ascii=False, indent=2))


def cmd_dataset_summary(args: argparse.Namespace) -> None:
    with open(args.path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    samples = payload.get("samples", payload)
    print(json.dumps(summarize_dataset(samples), ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="id-doc-ocr")
    sub = parser.add_subparsers(dest="command", required=True)

    p1 = sub.add_parser("list-plugins")
    p1.set_defaults(func=cmd_list_plugins)

    p2 = sub.add_parser("validate-plugin")
    p2.add_argument("name")
    p2.set_defaults(func=cmd_validate_plugin)

    p3 = sub.add_parser("dataset-summary")
    p3.add_argument("path")
    p3.set_defaults(func=cmd_dataset_summary)

    return parser


def main() -> None:
    from id_doc_ocr import plugins  # noqa: F401

    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
