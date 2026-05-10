"""Draw the ROI rectangle on a frame.

Pillow is used deliberately — the spec forbids OpenCV. Input/output are both
RGB ``numpy.ndarray`` so the caller can plug this between any frame source
and any frame sink without extra conversions.

Kept independent of ``face_detection`` on purpose: a Box is just an
``(x, y, w, h)`` tuple; the renderer should not pull in dlib.
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

ROI_COLOR = (0, 255, 0)  # bright green
ROI_WIDTH = 3            # pixels


def draw_roi(frame: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    """Return a copy of *frame* with the bounding *box* drawn on it."""
    x, y, w, h = box
    image = Image.fromarray(frame)
    draw = ImageDraw.Draw(image)
    draw.rectangle(
        [x, y, x + w, y + h],
        outline=ROI_COLOR,
        width=ROI_WIDTH,
    )
    return np.asarray(image)
