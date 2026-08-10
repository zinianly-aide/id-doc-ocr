from __future__ import annotations

from id_doc_ocr.leave_audit.worker.result_runtime import build_default_result_runtime


def main() -> None:
    build_default_result_runtime().run_forever()
