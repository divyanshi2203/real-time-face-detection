"""HTTP API blueprint.

Endpoints:

  POST /api/videos              upload a video file (mp4 / webm / mov)
  GET  /api/videos/<id>         stream the processed mp4 (with ROIs drawn)
  GET  /api/videos/<id>/rois    per-frame ROI data + video metadata as JSON

Processing runs synchronously inside ``POST /api/videos`` — see
``services.video_processor``.
"""
from __future__ import annotations

from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, send_file, url_for

from .errors import APIError
from .extensions import db
from .models import Video
from .services.video_processor import VideoProcessingError, process_video
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

    source, stored_name, size = store_upload(file, cfg["UPLOAD_DIR"])

    video = Video(
        original_filename=file.filename,
        stored_filename=stored_name,
        content_type=file.mimetype,
        size_bytes=size,
        status=Video.STATUS_UPLOADED,
    )
    db.session.add(video)
    db.session.commit()

    dest = Path(cfg["PROCESSED_DIR"]) / stored_name
    try:
        process_video(video, source, dest)
    except VideoProcessingError as exc:
        raise APIError(
            "processing_failed",
            str(exc) or "Video processing failed.",
            422,
        )

    response = jsonify(video.to_dict())
    response.status_code = 201
    response.headers["Location"] = url_for("api.get_video", video_id=video.id)
    return response


@api_bp.get("/videos/<int:video_id>")
def get_video(video_id: int):
    video = db.session.get(Video, video_id)
    if video is None:
        raise APIError("not_found", f"Video {video_id} not found.", 404)

    if video.status == Video.STATUS_FAILED:
        raise APIError(
            "processing_failed",
            video.error_message or "Video processing failed.",
            422,
        )
    if video.status != Video.STATUS_PROCESSED:
        raise APIError(
            "not_ready",
            f"Video is not ready yet (status={video.status!r}).",
            409,
        )

    processed_path = Path(current_app.config["PROCESSED_DIR"]) / video.stored_filename
    if not processed_path.exists():
        raise APIError(
            "not_found",
            "Processed video file is missing on disk.",
            404,
        )

    return send_file(
        processed_path,
        mimetype="video/mp4",
        conditional=True,  # enables HTTP Range requests for <video> seeking
    )


@api_bp.get("/videos/<int:video_id>/rois")
def get_video_rois(video_id: int):
    video = db.session.get(Video, video_id)
    if video is None:
        raise APIError("not_found", f"Video {video_id} not found.", 404)

    return jsonify({
        "video_id": video.id,
        "status": video.status,
        "fps": video.fps,
        "frame_count": video.frame_count,
        "width": video.width,
        "height": video.height,
        "rois": [r.to_dict() for r in video.rois.all()],
    })
