"""Single-face detection on a single frame.

Uses ``face_recognition`` (which wraps dlib's HOG detector). The task spec
guarantees at most one face per frame; if more are returned we pick the
largest one so a tiny background false-positive cannot push the real face
out of the result.
"""
from __future__ import annotations

from typing import Optional

import numpy as np

# (x, y, width, height) — axis-aligned, top-left origin, in pixels.
Box = tuple[int, int, int, int]


def detect_face_box(frame: np.ndarray) -> Optional[Box]:
    """Return the bounding box of the detected face, or ``None``."""
    # Imported lazily so that tests (and any reviewer running ``pytest``)
    # don't need dlib installed; the production image always does.
    import face_recognition

    locations = face_recognition.face_locations(frame, model="hog")
    if not locations:
        return None

    # face_recognition returns (top, right, bottom, left).
    def to_box(loc: tuple[int, int, int, int]) -> Box:
        top, right, bottom, left = loc
        return left, top, right - left, bottom - top

    boxes = [to_box(loc) for loc in locations]
    # If multiple are detected, keep the largest by area.
    return max(boxes, key=lambda b: b[2] * b[3])
