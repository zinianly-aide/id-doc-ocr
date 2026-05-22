#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path

from id_doc_ocr.leave_audit.repository.sqlite_repository import DEFAULT_DB_PATH, SQLiteRepository


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reset local leave_audit demo SQLite database.")
    parser.add_argument(
        "--db-path",
        default=os.getenv("ID_DOC_OCR_LEAVE_AUDIT_DB") or DEFAULT_DB_PATH,
        help="SQLite database path to reset. Defaults to ID_DOC_OCR_LEAVE_AUDIT_DB or .local/leave_audit.db.",
    )
    parser.add_argument(
        "--no-recreate",
        action="store_true",
        help="Only delete the database file; do not recreate an empty schema.",
    )
    return parser.parse_args()


def reset_database(db_path: str | Path, *, recreate: bool = True) -> Path:
    path = Path(db_path)
    if path.exists() and path.is_dir():
        raise IsADirectoryError(f"Refusing to remove directory: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    if recreate:
        SQLiteRepository(path)
    return path


def main() -> int:
    args = parse_args()
    path = reset_database(args.db_path, recreate=not args.no_recreate)
    print(f"Reset leave_audit demo database: {path}")
    if args.no_recreate:
        print("Schema recreation skipped; the API will recreate it on first repository use.")
    else:
        print("Empty leave_audit schema recreated.")
    print("Next demo commands:")
    print("  export ID_DOC_OCR_LEAVE_SYSTEM_ADAPTER=mock")
    print(f"  export ID_DOC_OCR_LEAVE_AUDIT_DB={path}")
    print("  python -m uvicorn id_doc_ocr.service.app:app --host 127.0.0.1 --port 8000")
    print("  curl -X POST http://127.0.0.1:8000/leave-audit/sync")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
