"""End-to-end tests for the HTTP API.

The face detector is monkey-patched in the happy-path tests so the suite
can run without dlib. Everything else (imageio reading, ffmpeg writing,
SQLAlchemy persistence, validation) is exercised for real.
"""
import io


# ---------- health ----------

def test_health_returns_ok(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json() == {"status": "ok"}


# ---------- upload validation ----------

def test_upload_rejects_missing_field(client):
    res = client.post("/api/videos")
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "missing_file"


def test_upload_rejects_blank_filename(client):
    data = {"video": (io.BytesIO(b""), "")}
    res = client.post("/api/videos", data=data, content_type="multipart/form-data")
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "missing_file"


def test_upload_rejects_disallowed_extension(client):
    data = {"video": (io.BytesIO(b"hi"), "evil.txt", "text/plain")}
    res = client.post("/api/videos", data=data, content_type="multipart/form-data")
    assert res.status_code == 415
    assert res.get_json()["error"]["code"] == "unsupported_media_type"


def test_upload_rejects_disallowed_mimetype(client):
    data = {"video": (io.BytesIO(b"hi"), "clip.mp4", "application/octet-stream")}
    res = client.post("/api/videos", data=data, content_type="multipart/form-data")
    assert res.status_code == 415


def test_upload_rejects_oversized_payload(client, app):
    # MAX_UPLOAD_MB is 5 in the test config.
    big = b"\0" * (app.config["MAX_UPLOAD_MB"] * 1024 * 1024 + 1)
    data = {"video": (io.BytesIO(big), "clip.mp4", "video/mp4")}
    res = client.post("/api/videos", data=data, content_type="multipart/form-data")
    assert res.status_code == 413
    assert res.get_json()["error"]["code"] == "payload_too_large"


def test_upload_returns_422_for_unprocessable_video(client):
    data = {"video": (io.BytesIO(b"not-a-real-mp4"), "clip.mp4", "video/mp4")}
    res = client.post("/api/videos", data=data, content_type="multipart/form-data")
    assert res.status_code == 422
    assert res.get_json()["error"]["code"] == "processing_failed"


# ---------- 404 / 405 ----------

def test_get_unknown_video(client):
    res = client.get("/api/videos/9999")
    assert res.status_code == 404
    assert res.get_json()["error"]["code"] == "not_found"


def test_get_unknown_video_rois(client):
    res = client.get("/api/videos/9999/rois")
    assert res.status_code == 404


def test_method_not_allowed(client):
    res = client.put("/api/videos")
    assert res.status_code == 405
    assert res.get_json()["error"]["code"] == "method_not_allowed"


# ---------- happy path ----------

def test_upload_happy_path_persists_rois_and_serves_processed_video(
    client, monkeypatch, upload_payload,
):
    # Avoid pulling in dlib in tests — return a fixed bounding box for every frame.
    from app.services import video_processor
    monkeypatch.setattr(
        video_processor, "detect_face_box", lambda _frame: (10, 20, 30, 40),
    )

    res = client.post(
        "/api/videos", data=upload_payload(), content_type="multipart/form-data",
    )
    assert res.status_code == 201
    body = res.get_json()
    assert body["status"] == "processed"
    assert body["frame_count"] == 5
    assert body["fps"] == 10.0
    assert body["width"] == 160 and body["height"] == 90
    assert res.headers["Location"].endswith(f"/api/videos/{body['id']}")

    # Streamed processed mp4
    res = client.get(f"/api/videos/{body['id']}")
    assert res.status_code == 200
    assert res.headers["Content-Type"] == "video/mp4"
    assert len(res.data) > 0

    # ROI listing
    res = client.get(f"/api/videos/{body['id']}/rois")
    assert res.status_code == 200
    rois = res.get_json()
    assert rois["frame_count"] == 5
    assert len(rois["rois"]) == 5
    first = rois["rois"][0]
    assert first == {"frame": 0, "t_ms": 0, "x": 10, "y": 20, "w": 30, "h": 40}
    # Frames are emitted at fps=10 → 100 ms apart.
    assert rois["rois"][1]["t_ms"] == 100


def test_upload_succeeds_with_no_face_in_any_frame(
    client, monkeypatch, upload_payload,
):
    from app.services import video_processor
    monkeypatch.setattr(video_processor, "detect_face_box", lambda _frame: None)

    res = client.post(
        "/api/videos", data=upload_payload(), content_type="multipart/form-data",
    )
    assert res.status_code == 201
    body = res.get_json()
    assert body["status"] == "processed"

    res = client.get(f"/api/videos/{body['id']}/rois")
    payload = res.get_json()
    assert payload["frame_count"] == 5
    assert payload["rois"] == []
