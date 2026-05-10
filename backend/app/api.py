"""HTTP API blueprint.

Endpoints landing in this commit:

  POST /api/videos      -> upload a video file (mp4 / webm / mov)
  GET  /api/videos/<id> -> metadata for a video (placeholder; commit 3 streams
                           the processed mp4 from this same URL)

The detection pipeline and the per-frame ROI endpoint are wired up in the
next commit.
"""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request, url_for

from .errors import APIError
from .extensions import db
from .models import Video
from .storage import safe_extension, store_upload

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.post("/videos")
def upload_video():
    if "video" not in request.files:
        raise APIError(
            "missing_file",
            "Multipart form field 'video' is required.",
            400,
        )

    file = request.files["video"]
    if not file or not file.filename:
        raise APIError("missing_file", "No file selected.", 400)

    cfg = current_app.config
    ext = safe_extension(file.filename)

    if ext not in cfg["ALLOWED_VIDEO_EXTENSIONS"]:
        allowed = ", ".join(sorted(cfg["ALLOWED_VIDEO_EXTENSIONS"]))
        raise APIError(
            "unsupported_media_type",
            f"Extension '.{ext}' is not allowed. Allowed: {allowed}.",
            415,
        )

    if file.mimetype not in cfg["ALLOWED_VIDEO_MIMETYPES"]:
        raise APIError(
            "unsupported_media_type",
            f"Content-Type '{file.mimetype}' is not allowed.",
            415,
        )

    _, stored_name, size = store_upload(file, cfg["UPLOAD_DIR"])

    video = Video(
        original_filename=file.filename,
        stored_filename=stored_name,
        content_type=file.mimetype,
        size_bytes=size,
        status=Video.STATUS_UPLOADED,
    )
    db.session.add(video)
    db.session.commit()

    response = jsonify(video.to_dict())
    response.status_code = 201
    response.headers["Location"] = url_for("api.get_video", video_id=video.id)
    return response


@api_bp.get("/videos/<int:video_id>")
def get_video(video_id: int):
    video = db.session.get(Video, video_id)
    if video is None:
        raise APIError("not_found", f"Video {video_id} not found.", 404)
    # Streaming the processed mp4 lands in the next commit.
    return jsonify(video.to_dict())
