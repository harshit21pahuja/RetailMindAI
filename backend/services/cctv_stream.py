"""
Phase 5 — CCTV / Video Ingestion Service
==========================================
Handles frame-by-frame product detection from:
  - Local video files (MP4, AVI, MOV, MKV)
  - Webcam / live RTSP streams (by index or URL)

Design decisions:
  - Frame sampling at configurable FPS (default: 1 frame every 5 seconds)
    to balance accuracy vs. processing speed without GPU.
  - Each sampled frame is passed through the vision_service YOLO pipeline.
  - Aggregated detection counts are returned (per-frame + overall summary).
  - No real-time streaming to the browser — the system processes the file
    asynchronously and stores summary results.
  - CCTV analysis is clearly labelled as "visible shelf stock observation",
    not a claim of total physical inventory.
"""

from __future__ import annotations

import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.config import settings


class CCTVStreamService:
    """
    Processes video files or webcam streams frame-by-frame to detect products.

    Notes:
      - OpenCV is loaded lazily so the backend starts without it if not installed.
      - YOLO inference is delegated to the existing VisionService to reuse
        the loaded model and annotation logic.
    """

    def __init__(self) -> None:
        self._results_dir = Path(settings.DETECTION_RESULTS_DIR) / "cctv"
        self._results_dir.mkdir(parents=True, exist_ok=True)

    # ── Public: process a video file ──────────────────────────────────────────

    def process_video_file(
        self,
        video_path: str,
        sample_interval_seconds: float = 5.0,
        max_frames: int = 50,
        save_annotated_frames: bool = True,
    ) -> Dict[str, Any]:
        """
        Process a video file and run YOLO detection on sampled frames.

        Args:
            video_path: Absolute or relative path to the video file.
            sample_interval_seconds: Time gap between analysed frames (default 5 s).
            max_frames: Hard cap on the number of frames processed (default 50).
            save_annotated_frames: Whether to save annotated JPEG snapshots.

        Returns:
            A dict with per-frame detections and an aggregated summary.
        """
        try:
            import cv2
        except ImportError:
            raise RuntimeError(
                "OpenCV is not installed. Run: pip install opencv-python-headless"
            )

        from backend.services.vision_service import vision_service

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video file: {video_path}")

        try:
            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration_seconds = total_frames / fps if fps > 0 else 0

            # Compute which frame indices to sample
            frame_step = max(1, int(fps * sample_interval_seconds))
            sample_indices = list(range(0, total_frames, frame_step))[:max_frames]

            session_id = str(uuid.uuid4())[:8]
            frame_results: List[Dict[str, Any]] = []
            aggregated_counts: Dict[str, int] = {}

            for frame_idx in sample_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if not ret:
                    break

                timestamp_sec = frame_idx / fps

                # Run YOLO on the frame (convert BGR→RGB for YOLO)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                detection = vision_service.detect_from_array(frame_rgb)

                # Optionally save annotated frame
                annotated_path: Optional[str] = None
                annotated_url: Optional[str] = None
                if save_annotated_frames and detection.get("annotated_image_array") is not None:
                    frame_filename = self._results_dir / f"{session_id}_f{frame_idx:06d}.jpg"
                    cv2.imwrite(str(frame_filename), detection["annotated_image_array"])
                    annotated_path = str(frame_filename)
                    annotated_url = f"/static/detections/cctv/{frame_filename.name}"

                frame_result = {
                    "frame_index": frame_idx,
                    "timestamp_sec": round(timestamp_sec, 2),
                    "timestamp_label": _format_seconds(timestamp_sec),
                    "detections": detection.get("detections", []),
                    "total_detected": detection.get("total_detected", 0),
                    "counts_per_class": detection.get("counts_per_class", {}),
                    "annotated_frame_path": annotated_path,
                    "annotated_frame_url": annotated_url,
                }
                frame_results.append(frame_result)

                # Merge into aggregated counts (max per class across all frames,
                # as this approximates peak visible shelf stock)
                for cls, cnt in detection.get("counts_per_class", {}).items():
                    aggregated_counts[cls] = max(aggregated_counts.get(cls, 0), cnt)
        finally:
            cap.release()

        return {
            "session_id": session_id,
            "source": "VIDEO_FILE",
            "video_path": video_path,
            "video_fps": round(fps, 2),
            "video_duration_sec": round(duration_seconds, 2),
            "total_video_frames": total_frames,
            "frames_sampled": len(frame_results),
            "frames_analyzed": len(frame_results),
            "sample_interval_sec": sample_interval_seconds,
            "max_frames_cap": max_frames,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "frame_results": frame_results,
            "aggregated_counts": aggregated_counts,
            "peak_visible_counts": aggregated_counts,
            "aggregated_total": sum(aggregated_counts.values()),
            "caveat": (
                "Counts represent PEAK VISIBLE SHELF STOCK detected across sampled frames. "
                "This is NOT a measure of total physical inventory — backroom and "
                "non-visible stock are not included."
            ),
        }

    # ── Public: process a webcam/stream ───────────────────────────────────────

    def process_live_stream(
        self,
        source: int | str = 0,
        duration_seconds: float = 30.0,
        sample_interval_seconds: float = 5.0,
        max_frames: int = 20,
        save_annotated_frames: bool = True,
    ) -> Dict[str, Any]:
        """
        Capture `duration_seconds` from a webcam or RTSP stream and analyse sampled frames.

        Args:
            source: Webcam index (int, e.g. 0) or RTSP URL string.
            duration_seconds: How long to record before stopping.
            sample_interval_seconds: Seconds between analysed frames.
            max_frames: Hard cap on frames to analyse.
            save_annotated_frames: Whether to save annotated JPEG snapshots.

        Returns:
            Same structure as process_video_file().
        """
        try:
            import cv2
        except ImportError:
            raise RuntimeError(
                "OpenCV is not installed. Run: pip install opencv-python-headless"
            )

        from backend.services.vision_service import vision_service

        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open stream source: {source}")

        try:
            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            session_id = str(uuid.uuid4())[:8]
            frame_results: List[Dict[str, Any]] = []
            aggregated_counts: Dict[str, int] = {}

            start_time = time.time()
            last_sampled = start_time - sample_interval_seconds  # sample immediately
            frame_count = 0

            while True:
                elapsed = time.time() - start_time
                if elapsed >= duration_seconds:
                    break
                if len(frame_results) >= max_frames:
                    break

                ret, frame = cap.read()
                if not ret:
                    break
                frame_count += 1

                # Only analyse every N seconds
                now = time.time()
                if (now - last_sampled) < sample_interval_seconds:
                    continue
                last_sampled = now

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                detection = vision_service.detect_from_array(frame_rgb)

                annotated_path: Optional[str] = None
                annotated_url: Optional[str] = None
                if save_annotated_frames and detection.get("annotated_image_array") is not None:
                    frame_filename = self._results_dir / f"{session_id}_t{elapsed:.1f}s.jpg"
                    cv2.imwrite(str(frame_filename), detection["annotated_image_array"])
                    annotated_path = str(frame_filename)
                    annotated_url = f"/static/detections/cctv/{frame_filename.name}"

                frame_results.append({
                    "frame_index": frame_count,
                    "timestamp_sec": round(elapsed, 2),
                    "timestamp_label": _format_seconds(elapsed),
                    "detections": detection.get("detections", []),
                    "total_detected": detection.get("total_detected", 0),
                    "counts_per_class": detection.get("counts_per_class", {}),
                    "annotated_frame_path": annotated_path,
                    "annotated_frame_url": annotated_url,
                })

                for cls, cnt in detection.get("counts_per_class", {}).items():
                    aggregated_counts[cls] = max(aggregated_counts.get(cls, 0), cnt)
        finally:
            cap.release()

        return {
            "session_id": session_id,
            "source": f"LIVE_STREAM:{source}",
            "capture_duration_sec": round(time.time() - start_time, 2),
            "frames_captured": frame_count,
            "frames_sampled": len(frame_results),
            "frames_analyzed": len(frame_results),
            "sample_interval_sec": sample_interval_seconds,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "frame_results": frame_results,
            "aggregated_counts": aggregated_counts,
            "peak_visible_counts": aggregated_counts,
            "aggregated_total": sum(aggregated_counts.values()),
            "caveat": (
                "Counts represent PEAK VISIBLE SHELF STOCK detected across sampled frames. "
                "This is NOT a measure of total physical inventory."
            ),
        }


# ── Module-level singleton ─────────────────────────────────────────────────────

cctv_stream_service = CCTVStreamService()


# ── Helper ─────────────────────────────────────────────────────────────────────

def _format_seconds(sec: float) -> str:
    """Format a seconds float as HH:MM:SS."""
    sec = int(sec)
    h, remainder = divmod(sec, 3600)
    m, s = divmod(remainder, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"
