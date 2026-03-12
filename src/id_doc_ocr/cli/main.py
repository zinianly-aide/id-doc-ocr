from __future__ import annotations

import argparse
import json

from id_doc_ocr.core.registry import registry
from id_doc_ocr.tools.dataset_quality import summarize_dataset
from id_doc_ocr.tools.manifest_ops import build_manifest, split_manifest


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




def cmd_manifest_build(args: argparse.Namespace) -> None:
    with open(args.path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    manifest = build_manifest(args.name, payload.get("samples", payload))
    print(manifest.model_dump_json(indent=2))


def cmd_manifest_split(args: argparse.Namespace) -> None:
    with open(args.path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    result = split_manifest(payload.get("samples", payload), train_ratio=args.train_ratio)
    print(json.dumps(result, ensure_ascii=False, indent=2))

def cmd_serve(args: argparse.Namespace) -> None:
    import uvicorn

    uvicorn.run(
        "id_doc_ocr.service.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


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

    p4 = sub.add_parser("manifest-build")
    p4.add_argument("name")
    p4.add_argument("path")
    p4.set_defaults(func=cmd_manifest_build)

    p5 = sub.add_parser("manifest-split")
    p5.add_argument("path")
    p5.add_argument("--train-ratio", type=float, default=0.8)
    p5.set_defaults(func=cmd_manifest_split)

    p6 = sub.add_parser("serve")
    p6.add_argument("--host", default="0.0.0.0")
    p6.add_argument("--port", type=int, default=8000)
    p6.add_argument("--reload", action="store_true")
    p6.set_defaults(func=cmd_serve)

    return parser


def main() -> None:
    from id_doc_ocr import plugins  # noqa: F401

    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


def main_api() -> None:
    import sys

    sys.argv = [sys.argv[0], "serve", *sys.argv[1:]]
    main()


if __name__ == "__main__":
    main()
