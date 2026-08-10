from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol


def sha256_hex(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


@dataclass(frozen=True, slots=True)
class StoredObject:
    object_key: str
    content_sha256: str
    size_bytes: int
    content_type: str | None = None


class ObjectStorage(Protocol):
    def put_bytes(self, object_key: str, content: bytes, *, content_type: str | None = None) -> StoredObject: ...

    def get_bytes(self, object_key: str) -> bytes: ...

    def head(self, object_key: str) -> StoredObject: ...
