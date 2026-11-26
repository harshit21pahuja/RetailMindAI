from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    x1: float = Field(..., description="Top-left x coordinate")
    y1: float = Field(..., description="Top-left y coordinate")
    x2: float = Field(..., description="Bottom-right x coordinate")
    y2: float = Field(..., description="Bottom-right y coordinate")
    width: float = Field(..., description="Box width in pixels")
    height: float = Field(..., description="Box height in pixels")


class DetectedItem(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    bbox: BoundingBox


class ShelfDetectionResponse(BaseModel):
    filename: str
    image_width: int
    image_height: int
    total_detected: int
    class_counts: Dict[str, int]
    detections: List[DetectedItem]
    annotated_image_url: str
    annotated_image_path: str
    model_name: str
    model_mode: str = Field(
        ...,
        description="Pipeline mode: GENERIC_PIPELINE_VALIDATION or CUSTOM_RETAIL_SKU"
    )
    disclaimer: str = Field(
        default=(
            "Generic pretrained YOLO is used for pipeline testing/validation. "
            "To distinguish fine-grained retail SKUs (e.g., Coke vs Pepsi), "
            "plug in custom-trained retail weights."
        )
    )
    inference_time_ms: float
