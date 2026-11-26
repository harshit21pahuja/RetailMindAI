import io
import os
from pathlib import Path
import pytest
from httpx import AsyncClient
from PIL import Image, ImageDraw


def create_test_image_bytes(format: str = "JPEG") -> bytes:
    """Generate an in-memory sample image with shapes representing products."""
    img = Image.new("RGB", (640, 480), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    # Draw simulated bottle shapes / rectangular packages
    draw.rectangle([100, 150, 180, 400], fill=(220, 50, 50), outline=(0, 0, 0))    # Red bottle/pack
    draw.rectangle([220, 150, 300, 400], fill=(50, 100, 220), outline=(0, 0, 0))   # Blue bottle/pack
    draw.rectangle([340, 200, 440, 400], fill=(50, 200, 50), outline=(0, 0, 0))    # Green pack
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_vision_model_info(async_client: AsyncClient):
    """Test retrieving active YOLO model information."""
    response = await async_client.get("/api/v1/vision/model-info")
    assert response.status_code == 200
    data = response.json()
    assert "model_path" in data
    assert "model_mode" in data
    assert "confidence_threshold" in data
    assert "custom_weights_guide" in data
    assert data["model_mode"] in ["GENERIC_PIPELINE_VALIDATION", "CUSTOM_RETAIL_SKU"]


@pytest.mark.asyncio
async def test_detect_shelf_unsupported_format(async_client: AsyncClient):
    """Test rejection of non-image file extensions."""
    files = {"file": ("report.pdf", b"%PDF-1.4 dummy content", "application/pdf")}
    response = await async_client.post("/api/v1/vision/detect-shelf", files=files)
    assert response.status_code == 415
    assert "Unsupported file format" in response.json()["detail"]


@pytest.mark.asyncio
async def test_detect_shelf_empty_file(async_client: AsyncClient):
    """Test rejection of 0-byte file upload."""
    files = {"file": ("empty.jpg", b"", "image/jpeg")}
    response = await async_client.post("/api/v1/vision/detect-shelf", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_detect_shelf_valid_image(async_client: AsyncClient):
    """Test complete YOLO shelf detection on a valid JPEG image."""
    image_bytes = create_test_image_bytes(format="JPEG")
    files = {"file": ("test_shelf.jpg", image_bytes, "image/jpeg")}

    response = await async_client.post("/api/v1/vision/detect-shelf?conf_threshold=0.20", files=files)
    assert response.status_code == 200
    data = response.json()

    # Validate top-level response schema
    assert data["filename"] == "test_shelf.jpg"
    assert data["image_width"] == 640
    assert data["image_height"] == 480
    assert isinstance(data["total_detected"], int)
    assert isinstance(data["class_counts"], dict)
    assert isinstance(data["detections"], list)
    assert "annotated_image_url" in data
    assert "annotated_image_path" in data
    assert data["annotated_image_url"].startswith("/static/detections/")
    assert data["inference_time_ms"] > 0
    assert "disclaimer" in data

    # Verify that the annotated image was written to disk
    annotated_path = Path(data["annotated_image_path"])
    assert annotated_path.exists()
    assert annotated_path.stat().st_size > 0


@pytest.mark.asyncio
async def test_detect_shelf_png_format(async_client: AsyncClient):
    """Test detection works equally on PNG format uploads."""
    png_bytes = create_test_image_bytes(format="PNG")
    files = {"file": ("shelf_inventory.png", png_bytes, "image/png")}

    response = await async_client.post("/api/v1/vision/detect-shelf", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "shelf_inventory.png"
    assert Path(data["annotated_image_path"]).exists()
