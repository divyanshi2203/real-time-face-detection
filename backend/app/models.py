"""Persistence model.

Two tables — kept intentionally small. SQLite is the right tool for a
single-instance app like this; no migration tool is used, ``db.create_all()``
runs once at startup.

Lifecycle of a ``Video.status``::

    uploaded -> processing -> processed
                          \\-> failed
"""
from datetime import datetime, timezone

from .extensions import db


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Video(db.Model):
    __tablename__ = "videos"

    STATUS_UPLOADED = "uploaded"
    STATUS_PROCESSING = "processing"
    STATUS_PROCESSED = "processed"
    STATUS_FAILED = "failed"

    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    content_type = db.Column(db.String(100), nullable=False)
    size_bytes = db.Column(db.BigInteger, nullable=False)

    status = db.Column(db.String(20), nullable=False, default=STATUS_UPLOADED)

    fps = db.Column(db.Float, nullable=True)
    frame_count = db.Column(db.Integer, nullable=True)
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)

    error_message = db.Column(db.Text, nullable=True)

    uploaded_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)

    rois = db.relationship(
        "ROIFrame",
        backref="video",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="ROIFrame.frame_number",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "original_filename": self.original_filename,
            "status": self.status,
            "content_type": self.content_type,
            "size_bytes": self.size_bytes,
            "fps": self.fps,
            "frame_count": self.frame_count,
            "width": self.width,
            "height": self.height,
            "error_message": self.error_message,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }

    def __repr__(self) -> str:
        return f"<Video id={self.id} status={self.status!r}>"


class ROIFrame(db.Model):
    """Axis-aligned bounding box of the (single) detected face in one frame."""

    __tablename__ = "roi_frames"

    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(
        db.Integer,
        db.ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    frame_number = db.Column(db.Integer, nullable=False)
    timestamp_ms = db.Column(db.Integer, nullable=False)

    x = db.Column(db.Integer, nullable=False)
    y = db.Column(db.Integer, nullable=False)
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("video_id", "frame_number", name="uq_roi_video_frame"),
    )

    def to_dict(self) -> dict:
        return {
            "frame": self.frame_number,
            "t_ms": self.timestamp_ms,
            "x": self.x,
            "y": self.y,
            "w": self.width,
            "h": self.height,
        }

    def __repr__(self) -> str:
        return (
            f"<ROIFrame video={self.video_id} frame={self.frame_number} "
            f"box=({self.x},{self.y},{self.width},{self.height})>"
        )
