from __future__ import annotations

from id_doc_ocr.leave_audit.worker.runtime import build_default_runtime


def main() -> None:
    build_default_runtime().run_forever()

