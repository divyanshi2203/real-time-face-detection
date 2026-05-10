"""End-to-end video processing pipeline.

For each frame of the source video:

1. Detect the face (``face_detection.detect_face_box``).
2. Persist a ``ROIFrame`` row when a face was found.
3. Draw the rectangle on a copy of the frame (``frame_renderer.draw_roi``).
4. Append the (possibly annotated) frame to the output mp4.

Processing runs **synchronously** inside the upload request — see
``api.upload_video``. This is a deliberate pragmatism choice: avoiding a
job queue keeps the surface area small. The trade-off (long-running
requests) is documented in the README.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

import imageio.v2 as imageio

from ..extensions import db
from ..models import ROIFrame, Video
from .face_detection import detect_face_box
from .frame_renderer import draw_roi

logger = logging.getLogger(__name__)


class VideoProcessingError(RuntimeError):
    """Raised when the source video cannot be processed."""


def process_video(video: Video, source: Path, dest: Path) -> None:
    """Process *source* and write the annotated mp4 to *dest*.

    Mutates *video* (status, fps, dimensions, frame count, processed_at)
    and inserts ``ROIFrame`` rows. On any failure the video is marked
    ``failed`` with ``error_message`` and a :class:`VideoProcessingError`
    is raised so the caller can choose the HTTP status.
    """
    video.status = Video.STATUS_PROCESSING
    db.session.commit()

    reader = None
    writer = None
    try:
        reader = imageio.get_reader(str(source), "ffmpeg")
        meta = reader.get_meta_data()

        fps = float(meta.get("fps") or 30.0)
        size = meta.get("size") or (None, None)
        width, height = (int(size[0]), int(size[1])) if all(size) else (None, None)

        dest.parent.mkdir(parents=True, exist_ok=True)
        writer = imageio.get_writer(
            str(dest),
            fps=fps,
            codec="libx264",
            quality=8,
            macro_block_size=1,  # don't force frame dims to multiples of 16
        )

        roi_rows: list[ROIFrame] = []
        frame_count = 0

        for frame_index, frame in enumerate(reader):
            frame_count += 1
            timestamp_ms = int(round(frame_index * 1000.0 / fps))

            box = detect_face_box(frame)
            if box is not None:
                x, y, w, h = box
                roi_rows.append(ROIFrame(
                    video_id=video.id,
                    frame_number=frame_index,
                    timestamp_ms=timestamp_ms,
                    x=x, y=y, width=w, height=h,
                ))
                frame = draw_roi(frame, box)

            writer.append_data(frame)

        if frame_count == 0:
            raise VideoProcessingError("Source contains no readable frames.")

        if roi_rows:
            db.session.add_all(roi_rows)

        video.fps = fps
        video.frame_count = frame_count
        video.width = width
        video.height = height
        video.status = Video.STATUS_PROCESSED
        video.processed_at = datetime.now(timezone.utc)
        db.session.commit()

    except VideoProcessingError as exc:
        _mark_failed(video, str(exc))
        raise
    except Exception as exc:
        logger.exception("Video processing failed for video id=%s", video.id)
        _mark_failed(video, str(exc) or exc.__class__.__name__)
        raise VideoProcessingError(str(exc)) from exc
    finally:
        if reader is not None:
            reader.close()
        if writer is not None:
            writer.close()


def _mark_failed(video: Video, message: str) -> None:
    db.session.rollback()
    video.status = Video.STATUS_FAILED
    video.error_message = message[:500]
    db.session.commit()
