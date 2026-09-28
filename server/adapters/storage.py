"""Object storage abstraction for listing images.

Does not store binaries in the database. Configure S3-compatible storage via env.
When not configured, upload endpoints return 503 with a clear error.
"""
from __future__ import annotations

import hashlib
import secrets
from pathlib import Path

from config import (
    ALLOWED_IMAGE_TYPES,
    MAX_UPLOAD_BYTES,
    OBJECT_STORAGE_ACCESS_KEY,
    OBJECT_STORAGE_BUCKET,
    OBJECT_STORAGE_ENDPOINT,
    OBJECT_STORAGE_PROVIDER,
    OBJECT_STORAGE_PUBLIC_BASE,
    OBJECT_STORAGE_REGION,
    OBJECT_STORAGE_SECRET_KEY,
)


def storage_configured() -> bool:
    return bool(
        OBJECT_STORAGE_PROVIDER
        and OBJECT_STORAGE_BUCKET
        and OBJECT_STORAGE_ACCESS_KEY
        and OBJECT_STORAGE_SECRET_KEY
    )


def validate_image(content_type: str, size: int) -> None:
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError("invalid_file_type")
    if size <= 0 or size > MAX_UPLOAD_BYTES:
        raise ValueError("invalid_file_size")


def upload_image(data: bytes, content_type: str, listing_id: str) -> dict:
    """Returns { url, object_key }. Raises if storage not configured or invalid."""
    validate_image(content_type, len(data))
    if not storage_configured():
        raise RuntimeError("object_storage_not_configured")

    ext = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}[content_type]
    key = f"listings/{listing_id}/{secrets.token_hex(8)}.{ext}"

    if OBJECT_STORAGE_PROVIDER in ("s3", "minio", "r2"):
        try:
            import boto3  # type: ignore
        except ImportError as e:
            raise RuntimeError("boto3_required_for_s3") from e
        kwargs = {
            "aws_access_key_id": OBJECT_STORAGE_ACCESS_KEY,
            "aws_secret_access_key": OBJECT_STORAGE_SECRET_KEY,
            "region_name": OBJECT_STORAGE_REGION or "us-east-1",
        }
        if OBJECT_STORAGE_ENDPOINT:
            kwargs["endpoint_url"] = OBJECT_STORAGE_ENDPOINT
        client = boto3.client("s3", **kwargs)
        client.put_object(
            Bucket=OBJECT_STORAGE_BUCKET,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        if OBJECT_STORAGE_PUBLIC_BASE:
            url = f"{OBJECT_STORAGE_PUBLIC_BASE.rstrip('/')}/{key}"
        else:
            url = f"https://{OBJECT_STORAGE_BUCKET}.s3.amazonaws.com/{key}"
        return {"url": url, "object_key": key}

    raise RuntimeError(f"unsupported_provider:{OBJECT_STORAGE_PROVIDER}")
