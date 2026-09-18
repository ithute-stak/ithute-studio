from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

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


@dataclass(slots=True)
class LocalPdfStorage:
    root: Path
    name: str = "local"

    def _path(self, key: str) -> Path:
        clean = key.strip().lstrip("/")
        if not clean or ".." in Path(clean).parts:
            raise StorageError("Invalid storage key")
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


def get_pdf_storage() -> PdfStorage:
    settings = get_settings()
    backend = settings.storage_backend.lower().strip()
    if backend == "local":
        root = Path(settings.storage_root).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        return LocalPdfStorage(root=root)
    raise StorageError(
        f"PDF storage backend '{settings.storage_backend}' is not configured in this deployment"
    )
