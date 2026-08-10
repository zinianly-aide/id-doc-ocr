from __future__ import annotations

import os

from id_doc_ocr.leave_audit.storage.base import ObjectStorage
from id_doc_ocr.leave_audit.storage.local import LocalObjectStorage


def create_object_storage() -> ObjectStorage:
    backend = os.getenv("OBJECT_STORAGE_BACKEND", "local").strip().lower()
    if backend == "local":
        return LocalObjectStorage(os.getenv("OBJECT_STORAGE_LOCAL_ROOT", ".local/object-storage"))
    if backend in {"s3", "minio"}:
        from id_doc_ocr.leave_audit.storage.s3 import S3ObjectStorage

        return S3ObjectStorage()
    raise ValueError(f"unsupported OBJECT_STORAGE_BACKEND: {backend}")

