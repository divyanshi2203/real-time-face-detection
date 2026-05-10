"""Filesystem helpers for uploaded videos.

Files are stored under their own randomly generated name to avoid path
traversal and collisions; the original filename is preserved in the DB row.
"""
from __future__ import annotations

import secrets
from pathlib import Path

from werkzeug.datastructures import FileStorage


def safe_extension(filename: str | None) -> str:
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[1].lower()


def store_upload(file_storage: FileStorage, upload_dir: Path) -> tuple[Path, str, int]:
    """Persist *file_storage* under a random name.

    Returns ``(absolute_path, stored_filename, size_bytes)``.
    """
    upload_dir = Path(upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    ext = safe_extension(file_storage.filename)
    suffix = f".{ext}" if ext else ""
    stored_name = f"{secrets.token_hex(16)}{suffix}"
    dest = upload_dir / stored_name

    file_storage.save(dest)
    return dest, stored_name, dest.stat().st_size
