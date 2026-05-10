"""Unit tests for the ROI rendering primitive."""
import numpy as np

from app.services.frame_renderer import ROI_COLOR, draw_roi


def _black_frame(h: int = 100, w: int = 200) -> np.ndarray:
    return np.zeros((h, w, 3), dtype=np.uint8)


def test_draw_roi_paints_corners():
    out = draw_roi(_black_frame(), (40, 30, 50, 40))
    assert tuple(out[30, 40]) == ROI_COLOR  # top-left
    assert tuple(out[69, 89]) == ROI_COLOR  # bottom-right edge


def test_draw_roi_does_not_fill_interior():
    out = draw_roi(_black_frame(), (40, 30, 50, 40))
    # A pixel several rows inside the box should remain unpainted (outline only).
    assert tuple(out[50, 60]) == (0, 0, 0)


def test_draw_roi_does_not_touch_pixels_outside_box():
    out = draw_roi(_black_frame(), (40, 30, 50, 40))
    assert tuple(out[10, 10]) == (0, 0, 0)
    assert tuple(out[90, 150]) == (0, 0, 0)


def test_draw_roi_returns_a_new_array():
    """The renderer should not mutate the input frame in place."""
    frame = _black_frame()
    original = frame.copy()
    draw_roi(frame, (10, 10, 20, 20))
    assert np.array_equal(frame, original)
