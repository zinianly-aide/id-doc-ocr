from __future__ import annotations

import os
from typing import Any

from id_doc_ocr.leave_audit.storage.base import StoredObject, sha256_hex


class S3ObjectStorage:
    def __init__(
        self,
        *,
        endpoint: str | None = None,
        bucket: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        region: str | None = None,
        client: Any | None = None,
    ) -> None:
        self.bucket = bucket or os.getenv("OBJECT_STORAGE_BUCKET")
        if not self.bucket:
            raise ValueError("OBJECT_STORAGE_BUCKET is required for S3 storage")
        if client is not None:
            self.client = client
            return
        try:
            import boto3
        except ImportError as exc:  # pragma: no cover - optional runtime dependency
            raise RuntimeError("S3 support requires the 'object-storage' extra") from exc
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint or os.getenv("OBJECT_STORAGE_ENDPOINT") or None,
            aws_access_key_id=access_key or os.getenv("OBJECT_STORAGE_ACCESS_KEY"),
            aws_secret_access_key=secret_key or os.getenv("OBJECT_STORAGE_SECRET_KEY"),
            region_name=region or os.getenv("OBJECT_STORAGE_REGION") or "us-east-1",
        )

    def put_bytes(self, object_key: str, content: bytes, *, content_type: str | None = None) -> StoredObject:
        kwargs = {"Bucket": self.bucket, "Key": object_key, "Body": content}
        if content_type:
            kwargs["ContentType"] = content_type
        self.client.put_object(**kwargs)
        return StoredObject(object_key, sha256_hex(content), len(content), content_type)

    def get_bytes(self, object_key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=object_key)
        body = response["Body"]
        return body.read() if hasattr(body, "read") else bytes(body)

    def head(self, object_key: str) -> StoredObject:
        response = self.client.head_object(Bucket=self.bucket, Key=object_key)
        content = self.get_bytes(object_key)
        return StoredObject(object_key, sha256_hex(content), int(response.get("ContentLength", len(content))))
