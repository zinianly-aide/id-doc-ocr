from __future__ import annotations

from pathlib import Path

from id_doc_ocr.leave_audit.storage.base import StoredObject, sha256_hex


class LocalObjectStorage:
    """Filesystem-backed object storage for local development and tests."""

    def __init__(self, root: str | Path = ".local/object-storage") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, object_key: str) -> Path:
        normalized = str(object_key).strip().lstrip("/")
        if not normalized:
            raise ValueError("object_key is required")
        path = (self.root / normalized).resolve()
        root = self.root.resolve()
        if path != root and root not in path.parents:
            raise ValueError("object_key escapes object storage root")
        return path

    def put_bytes(self, object_key: str, content: bytes, *, content_type: str | None = None) -> StoredObject:
        path = self._resolve(object_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return StoredObject(object_key, sha256_hex(content), len(content), content_type)

    def get_bytes(self, object_key: str) -> bytes:
        path = self._resolve(object_key)
        try:
            return path.read_bytes()
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"object not found: {object_key}") from exc

    def head(self, object_key: str) -> StoredObject:
        content = self.get_bytes(object_key)
        return StoredObject(object_key, sha256_hex(content), len(content))
