from __future__ import annotations

import os
from pathlib import Path


def main() -> None:
    try:
        import psycopg
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise SystemExit("Install the postgres extra first: pip install -e '.[postgres]'") from exc

    dsn = os.getenv("DATABASE_URL") or os.getenv("ID_DOC_OCR_DATABASE_URL")
    if not dsn:
        raise SystemExit("DATABASE_URL or ID_DOC_OCR_DATABASE_URL is required")

    migration_dir = Path(__file__).resolve().parents[1] / "migrations" / "postgres"
    migration_files = sorted(migration_dir.glob("*.sql"))
    if not migration_files:
        raise SystemExit(f"No PostgreSQL migrations found in {migration_dir}")

    with psycopg.connect(dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migration (
                    version TEXT PRIMARY KEY,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
            for migration in migration_files:
                version = migration.stem
                cursor.execute("SELECT 1 FROM schema_migration WHERE version = %s", (version,))
                if cursor.fetchone():
                    continue
                cursor.execute(migration.read_text(encoding="utf-8"))
                cursor.execute("INSERT INTO schema_migration (version) VALUES (%s)", (version,))


if __name__ == "__main__":
    main()
