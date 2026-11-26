from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status

from backend.config import settings
from backend.schemas.vision import ShelfDetectionResponse
from backend.services.vision_service import vision_service

router = APIRouter(prefix="/vision", tags=["Computer Vision & Shelf Detection"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/jpg"}
MAX_FILE_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@router.post(
    "/detect-shelf",
    response_model=ShelfDetectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload Shelf Image and Run YOLO Detection",
    description=(
        "Upload a shelf photo (JPG, JPEG, PNG). Runs YOLO product detection, "
        "counts visible inventory, and generates an annotated image with bounding boxes. "
        "Supports custom retail SKU weights or pretrained pipeline validation model."
    ),
)
async def detect_shelf(
    file: UploadFile = File(..., description="Shelf or store image (JPG/PNG, max 15MB)"),
    conf_threshold: Optional[float] = Query(
        None,
        ge=0.05,
        le=0.95,
        description="Optional detection confidence threshold (defaults to 0.25)",
    ),
):
    """Process uploaded shelf image, detect visible items, and tally inventory."""
    # 1. Validate file extension
    file_ext = Path(file.filename or "").suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported file format '{file_ext}'. "
                f"Allowed formats are: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            ),
        )

    # 2. Validate MIME type if provided
    if file.content_type and file.content_type.lower() not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Invalid MIME type '{file.content_type}'. "
                "Expected image/jpeg or image/png."
            ),
        )

    # 3. Read image bytes and validate file size
    try:
        image_bytes = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(e)}",
        )

    if len(image_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    if len(image_bytes) > MAX_FILE_BYTES:
        max_mb = settings.MAX_UPLOAD_SIZE_MB
        actual_mb = round(len(image_bytes) / (1024 * 1024), 2)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({actual_mb} MB) exceeds maximum allowed limit of {max_mb} MB.",
        )

    # 4. Execute detection through VisionService
    try:
        response = vision_service.detect_shelf_image(
            image_bytes=image_bytes,
            filename=file.filename or "shelf_upload.jpg",
            conf_threshold=conf_threshold,
        )
        return response
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Computer Vision inference pipeline error: {str(err)}",
        )


@router.get(
    "/model-info",
    summary="YOLO Model Information & Capabilities",
    description="Inspect current active YOLO model path, classification mode, and custom SKU plug-in guide.",
)
async def get_model_info():
    """Retrieve active YOLO model status and plug-in configuration."""
    return {
        "model_path": settings.YOLO_MODEL_PATH,
        "model_mode": vision_service._model_mode,
        "confidence_threshold": settings.YOLO_CONFIDENCE_THRESHOLD,
        "results_directory": settings.DETECTION_RESULTS_DIR,
        "max_upload_size_mb": settings.MAX_UPLOAD_SIZE_MB,
        "custom_weights_guide": (
            "To use custom retail SKU weights: Place your fine-tuned 'best.pt' file into "
            "'backend/ml_weights/' and update 'YOLO_MODEL_PATH=backend/ml_weights/best.pt' in .env."
        ),
    }
