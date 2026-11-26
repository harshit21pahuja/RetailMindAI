"""
Phase 5 Tests — CCTV Stream & Video Ingestion Pipeline
"""

import os
from pathlib import Path
import pytest
from httpx import AsyncClient

from backend.services.cctv_stream import cctv_stream_service


@pytest.mark.asyncio
async def test_cctv_status_endpoint(async_client: AsyncClient):
    """Test the CCTV service availability and configuration status endpoint."""
    response = await async_client.get("/api/v1/cctv/status")
    assert response.status_code == 200
    data = response.json()
    assert "cctv_service_available" in data
    assert data["cctv_service_available"] is True
    assert "opencv_version" in data
    assert "supported_video_formats" in data
    assert ".mp4" in data["supported_video_formats"]
    assert data["max_video_size_mb"] == 200
    assert "note" in data


@pytest.mark.asyncio
async def test_cctv_analyze_video_unsupported_format(async_client: AsyncClient):
    """Test rejection of non-video file formats."""
    files = {"file": ("report.pdf", b"%PDF-1.4 dummy content", "application/pdf")}
    response = await async_client.post("/api/v1/cctv/analyze-video", files=files)
    assert response.status_code == 415
    assert "Unsupported file format" in response.json()["detail"]


@pytest.mark.asyncio
async def test_cctv_analyze_video_valid_file(async_client: AsyncClient):
    """Test video analysis on a generated sample CCTV video."""
    video_path = Path("sample_data/cctv_shelf_sample.mp4")
    assert video_path.exists(), "Sample video sample_data/cctv_shelf_sample.mp4 must exist"

    with open(video_path, "rb") as f:
        video_bytes = f.read()

    files = {"file": ("cctv_test.mp4", video_bytes, "video/mp4")}
    data = {
        "sample_interval_seconds": 3.0,
        "max_frames": 10,
        "save_annotated_frames": "true",
    }

    response = await async_client.post(
        "/api/v1/cctv/analyze-video",
        files=files,
        data=data,
    )
    assert response.status_code == 200
    result = response.json()

    assert result["source"] == "VIDEO_FILE"
    assert result["original_filename"] == "cctv_test.mp4"
    assert result["frames_sampled"] > 0
    assert result["video_duration_sec"] > 0
    assert "aggregated_counts" in result
    assert isinstance(result["aggregated_counts"], dict)
    assert "frame_results" in result
    assert len(result["frame_results"]) == result["frames_sampled"]

    # Verify frame item structure
    first_frame = result["frame_results"][0]
    assert "frame_index" in first_frame
    assert "timestamp_sec" in first_frame
    assert "counts_per_class" in first_frame
    assert "annotated_frame_url" in first_frame


def test_cctv_service_direct_execution():
    """Test CCTVStreamService direct file processing."""
    video_path = "sample_data/cctv_shelf_sample.mp4"
    res = cctv_stream_service.process_video_file(
        video_path=video_path,
        sample_interval_seconds=4.0,
        max_frames=5,
        save_annotated_frames=True,
    )
    assert res["source"] == "VIDEO_FILE"
    assert res["frames_sampled"] >= 1
    assert "aggregated_counts" in res
    assert "caveat" in res


def test_cctv_service_nonexistent_file():
    """Test CCTVStreamService behavior on nonexistent file."""
    with pytest.raises(FileNotFoundError):
        cctv_stream_service.process_video_file("nonexistent_video_path.mp4")
