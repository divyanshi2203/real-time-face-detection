"""Shared pytest fixtures.

Each test gets a freshly created Flask app pointed at a per-test ``tmp_path``
for uploads / processed videos / SQLite, so tests are fully isolated and can
run in any order (or in parallel).
"""
from __future__ import annotations

import io

import imageio.v2 as imageio
import numpy as np
import pytest

from app import create_app
from app.config import Config


@pytest.fixture
def app(tmp_path):
    class TestConfig(Config):
        TESTING = True
        DATA_DIR = tmp_path
        UPLOAD_DIR = tmp_path / "uploads"
        PROCESSED_DIR = tmp_path / "processed"
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'test.db'}"
        MAX_UPLOAD_MB = 5  # small enough to test the 413 path quickly
        SECRET_KEY = "test"

    return create_app(TestConfig)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def tiny_video_bytes(tmp_path):
    """Generate a 5-frame solid-colour mp4 in tmp and return its bytes."""
    path = tmp_path / "fixture.mp4"
    writer = imageio.get_writer(
        str(path), fps=10, codec="libx264",
        macro_block_size=1, quality=8,
    )
    try:
        for i in range(5):
            frame = np.full((90, 160, 3), 30 + i * 30, dtype=np.uint8)
            writer.append_data(frame)
    finally:
        writer.close()
    return path.read_bytes()


@pytest.fixture
def upload_payload(tiny_video_bytes):
    """Convenience: a multipart payload pointing at the fixture clip."""
    def _make(filename: str = "clip.mp4", mimetype: str = "video/mp4"):
        return {"video": (io.BytesIO(tiny_video_bytes), filename, mimetype)}
    return _make
