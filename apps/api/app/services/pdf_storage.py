from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import boto3
from botocore.exceptions import ClientError

from app.core.config import get_settings


class StorageError(RuntimeError):
    pass


class PdfStorage(Protocol):
    name: str

    def put_bytes(self, key: str, content: bytes) -> str: ...

    def get_bytes(self, key: str) -> bytes: ...

    def delete(self, key: str) -> None: ...

    def exists(self, key: str) -> bool: ...

    def materialize(self, key: str) -> Path: ...


def _clean_key(key: str) -> str:
    clean = key.strip().lstrip("/")
    if not clean or ".." in Path(clean).parts:
        raise StorageError("Invalid storage key")
    return clean


@dataclass(slots=True)
class LocalPdfStorage:
    root: Path
    name: str = "local"

    def _path(self, key: str) -> Path:
        clean = _clean_key(key)
        path = (self.root / clean).resolve()
        root = self.root.resolve()
        if root not in path.parents and path != root:
            raise StorageError("Storage key escaped the configured root")
        return path

    def put_bytes(self, key: str, content: bytes) -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return key

    def get_bytes(self, key: str) -> bytes:
        path = self._path(key)
        if not path.exists():
            raise StorageError("Stored object is unavailable")
        return path.read_bytes()

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()
        parent = path.parent
        root = self.root.resolve()
        while parent != root and root in parent.parents:
            try:
                parent.rmdir()
            except OSError:
                break
            parent = parent.parent

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def materialize(self, key: str) -> Path:
        path = self._path(key)
        if not path.exists():
            raise StorageError("Stored object is unavailable")
        return path


@dataclass(slots=True)
class S3CompatiblePdfStorage:
    bucket: str
    cache_root: Path
    endpoint_url: str | None
    region: str | None
    access_key: str
    secret_key: str
    name: str = "s3"

    def _client(self):
        return boto3.client(
            "s3",
            endpoint_url=self.endpoint_url or None,
            region_name=self.region or None,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

    def put_bytes(self, key: str, content: bytes) -> str:
        clean = _clean_key(key)
        try:
            self._client().put_object(Bucket=self.bucket, Key=clean, Body=content)
        except ClientError as exc:
            raise StorageError("Object storage upload failed") from exc
        return clean

    def get_bytes(self, key: str) -> bytes:
        clean = _clean_key(key)
        try:
            response = self._client().get_object(Bucket=self.bucket, Key=clean)
            return response["Body"].read()
        except ClientError as exc:
            raise StorageError("Stored object is unavailable") from exc

    def delete(self, key: str) -> None:
        clean = _clean_key(key)
        try:
            self._client().delete_object(Bucket=self.bucket, Key=clean)
        except ClientError as exc:
            raise StorageError("Object storage delete failed") from exc
        cached = self._cache_path(clean)
        if cached.exists():
            cached.unlink()

    def exists(self, key: str) -> bool:
        clean = _clean_key(key)
        try:
            self._client().head_object(Bucket=self.bucket, Key=clean)
            return True
        except ClientError as exc:
            status = int(exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode", 500))
            if status == 404:
                return False
            raise StorageError("Object storage availability check failed") from exc

    def _cache_path(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        suffix = Path(key).suffix or ".bin"
        return self.cache_root / f"{digest}{suffix}"

    def materialize(self, key: str) -> Path:
        clean = _clean_key(key)
        path = self._cache_path(clean)
        if path.exists():
            return path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.get_bytes(clean))
        return path


def get_pdf_storage() -> PdfStorage:
    settings = get_settings()
    backend = settings.storage_backend.lower().strip()
    root = Path(settings.storage_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    if backend == "local":
        return LocalPdfStorage(root=root)
    if backend in {"s3", "minio"}:
        return S3CompatiblePdfStorage(
            bucket=settings.object_storage_bucket,
            cache_root=root / "object-cache",
            endpoint_url=settings.object_storage_endpoint_url,
            region=settings.object_storage_region,
            access_key=settings.object_storage_access_key,
            secret_key=settings.object_storage_secret_key,
            name=backend,
        )
    raise StorageError(f"Unsupported PDF storage backend '{settings.storage_backend}'")
