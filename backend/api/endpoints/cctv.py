"""
Phase 5 — CCTV / Video Analysis API Endpoints
===============================================
Routes:
  POST /api/v1/cctv/analyze-video   — upload & analyse a video file
  POST /api/v1/cctv/analyze-webcam  — start a timed webcam capture session
  GET  /api/v1/cctv/status          — check if CCTV service is available (cv2 installed)
"""

from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
import os
import tempfile
from pathlib import Path

router = APIRouter(prefix="/cctv", tags=["CCTV & Video Analysis"])

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
MAX_VIDEO_SIZE_MB = 200


# ─── GET /cctv/status ─────────────────────────────────────────────────────────

@router.get("/status", summary="Check CCTV service availability")
async def cctv_status():
    """
    Returns whether OpenCV is installed (required for video analysis).
    Also reports what video sources are supported.
    """
    cv2_available = False
    cv2_version = None
    try:
        import cv2
        cv2_available = True
        cv2_version = cv2.__version__
    except ImportError:
        pass

    return {
        "cctv_service_available": cv2_available,
        "opencv_version": cv2_version,
        "supported_video_formats": list(ALLOWED_VIDEO_EXTENSIONS),
        "max_video_size_mb": MAX_VIDEO_SIZE_MB,
        "note": (
            "CCTV analysis detects VISIBLE SHELF STOCK only. "
            "Backroom and non-visible inventory are not observed by the camera."
        ),
        "install_hint": None if cv2_available else "pip install opencv-python-headless",
    }


# ─── POST /cctv/analyze-video ─────────────────────────────────────────────────

@router.post(
    "/analyze-video",
    summary="Upload and analyse a video file for shelf inventory",
    status_code=status.HTTP_200_OK,
)
async def analyze_video_file(
    file: UploadFile = File(..., description="Video file (MP4, AVI, MOV, MKV, WEBM)"),
    sample_interval_seconds: float = Form(
        5.0, ge=1.0, le=60.0,
        description="Seconds between sampled frames (default: 5)",
    ),
    max_frames: int = Form(
        50, ge=1, le=200,
        description="Maximum number of frames to analyse (default: 50)",
    ),
    save_annotated_frames: bool = Form(
        True, description="Save annotated JPEG snapshots to disk"
    ),
):
    """
    Upload a video file and run YOLO-based shelf product detection on sampled frames.

    The service samples one frame every `sample_interval_seconds` seconds (default 5 s)
    to balance accuracy and processing time. Peak visible counts per class are aggregated
    across all sampled frames.

    **Important:** Detected counts represent visible shelf-facing stock only. This is NOT
    a total physical inventory count.
    """
    # Check OpenCV
    try:
        import cv2  # noqa: F401
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenCV is not installed on this server. Install: pip install opencv-python-headless",
        )

    # Validate extension
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}",
        )

    # Read & size-check
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_VIDEO_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Video file is too large ({size_mb:.1f} MB). Maximum: {MAX_VIDEO_SIZE_MB} MB",
        )

    # Write to temp file (OpenCV needs a real file path)
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        from backend.services.cctv_stream import cctv_stream_service
        result = cctv_stream_service.process_video_file(
            video_path=tmp_path,
            sample_interval_seconds=sample_interval_seconds,
            max_frames=max_frames,
            save_annotated_frames=save_annotated_frames,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except OSError:
            pass

    result["original_filename"] = file.filename
    return result


# ─── POST /cctv/analyze-webcam ────────────────────────────────────────────────

@router.post(
    "/analyze-webcam",
    summary="Run a timed webcam capture and analyse visible shelf products",
    status_code=status.HTTP_200_OK,
)
async def analyze_webcam(
    camera_index: int = Form(0, ge=0, description="Webcam device index (default: 0)"),
    duration_seconds: float = Form(
        30.0, ge=5.0, le=300.0, description="How many seconds to capture (default: 30)"
    ),
    sample_interval_seconds: float = Form(
        5.0, ge=1.0, le=60.0, description="Seconds between sampled frames (default: 5)"
    ),
    max_frames: int = Form(20, ge=1, le=100),
):
    """
    Open the webcam at `camera_index`, capture for `duration_seconds`, and run
    YOLO on sampled frames.

    Returns the same structure as `/analyze-video`.
    """
    try:
        import cv2  # noqa: F401
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenCV is not installed. Install: pip install opencv-python-headless",
        )

    try:
        from backend.services.cctv_stream import cctv_stream_service
        result = cctv_stream_service.process_live_stream(
            source=camera_index,
            duration_seconds=duration_seconds,
            sample_interval_seconds=sample_interval_seconds,
            max_frames=max_frames,
            save_annotated_frames=True,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return result
