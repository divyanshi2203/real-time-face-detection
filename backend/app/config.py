"""Application configuration.

All settings can be overridden via environment variables (see ``.env.example``).
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
DEFAULT_DATA_DIR = BASE_DIR.parent / "data"


def _path_env(name: str, default: Path) -> Path:
    return Path(os.environ.get(name, str(default)))


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    try:
        return int(raw) if raw is not None else default
    except ValueError:
        return default


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # Storage layout
    DATA_DIR = _path_env("DATA_DIR", DEFAULT_DATA_DIR)
    UPLOAD_DIR = _path_env("UPLOAD_DIR", DATA_DIR / "uploads")
    PROCESSED_DIR = _path_env("PROCESSED_DIR", DATA_DIR / "processed")

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{DATA_DIR / 'app.db'}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload constraints. ``MAX_CONTENT_LENGTH`` is derived from
    # ``MAX_UPLOAD_MB`` inside the app factory so that subclassing this
    # config in tests (just changing ``MAX_UPLOAD_MB``) does the right thing.
    MAX_UPLOAD_MB = _int_env("MAX_UPLOAD_MB", 50)

    ALLOWED_VIDEO_EXTENSIONS = frozenset({"mp4", "webm", "mov"})
    ALLOWED_VIDEO_MIMETYPES = frozenset({
        "video/mp4",
        "video/webm",
        "video/quicktime",
    })
