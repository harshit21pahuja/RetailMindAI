import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image

from backend.config import settings
from backend.schemas.vision import (
    BoundingBox,
    DetectedItem,
    ShelfDetectionResponse,
)


class VisionService:
    """Modular Computer Vision Service for Shelf Product Detection & Counting.

    Supports both:
    1. Pretrained standard YOLO models (e.g. yolov8n.pt) for pipeline sanity testing.
    2. Custom-trained retail SKU models (e.g. backend/ml_weights/retail_sku.pt) for
       fine-grained product recognition (Coke, Pepsi, Maggi, etc.).
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or settings.YOLO_MODEL_PATH
        self._model = None
        self._model_mode = "GENERIC_PIPELINE_VALIDATION"
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure results directories exist."""
        results_dir = Path(settings.DETECTION_RESULTS_DIR)
        results_dir.mkdir(parents=True, exist_ok=True)

        ml_weights_dir = Path("backend/ml_weights")
        ml_weights_dir.mkdir(parents=True, exist_ok=True)

    @property
    def model(self):
        """Lazy loader for YOLO model to prevent slow startup."""
        if self._model is None:
            self._load_model()
        return self._model

    def _load_model(self) -> None:
        """Load YOLO model checkpoint and determine classification capability."""
        from ultralytics import YOLO

        print(f"Loading YOLO model checkpoint from: {self.model_path}")
        
        # Resolve custom weights inside backend/ml_weights if relative path provided
        candidate_path = Path(self.model_path)
        if not candidate_path.exists() and (Path("backend/ml_weights") / self.model_path).exists():
            candidate_path = Path("backend/ml_weights") / self.model_path

        self._model = YOLO(str(candidate_path))

        # Check if the model has custom retail SKU classes or default COCO classes
        class_names = list(self._model.names.values()) if hasattr(self._model, "names") else []
        
        # If classes include typical fine-grained retail indicators
        retail_keywords = {"coke", "pepsi", "maggi", "kurkure", "lays", "parle", "amul", "sku", "product"}
        detected_retail_classes = [c for c in class_names if any(k in str(c).lower() for k in retail_keywords)]

        if detected_retail_classes:
            self._model_mode = "CUSTOM_RETAIL_SKU"
            print(f"Loaded Custom Retail YOLO Model ({len(class_names)} classes).")
        else:
            self._model_mode = "GENERIC_PIPELINE_VALIDATION"
            print(
                f"Loaded Pretrained Pipeline Model ({len(class_names)} COCO classes). "
                "Note: Pretrained COCO detects generic containers (bottles, cups, boxes); "
                "custom-trained weights are required for SKU-level brand distinction."
            )

    def decode_image_bytes(self, image_bytes: bytes) -> np.ndarray:
        """Safely decode raw image bytes to OpenCV BGR numpy array."""
        if not image_bytes:
            raise ValueError("Uploaded image file is empty (0 bytes).")

        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            # Fallback to PIL in case of esoteric image format headers
            import io
            try:
                pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
                img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            except Exception as e:
                raise ValueError(f"Unable to decode image file. Ensure it is a valid JPG/PNG format. Error: {e}")

        if img.shape[0] == 0 or img.shape[1] == 0:
            raise ValueError("Decoded image has zero width or height.")

        return img

    def detect_shelf_image(
        self,
        image_bytes: bytes,
        filename: str,
        conf_threshold: Optional[float] = None,
    ) -> ShelfDetectionResponse:
        """Run YOLO inference, count visible products, and produce annotated visual result."""
        start_time = time.perf_counter()

        confidence = conf_threshold if conf_threshold is not None else settings.YOLO_CONFIDENCE_THRESHOLD
        img_bgr = self.decode_image_bytes(image_bytes)
        height, width = img_bgr.shape[:2]

        # Execute YOLO prediction
        results = self.model.predict(
            source=img_bgr,
            conf=confidence,
            verbose=False,
        )

        detections: List[DetectedItem] = []
        class_counts: Dict[str, int] = {}

        # Copy image for custom visual bounding-box annotation
        annotated_img = img_bgr.copy()

        # Distinct color palette for bounding boxes (BGR)
        palette = [
            (46, 204, 113),  # Emerald Green
            (52, 152, 219),  # Peter River Blue
            (155, 89, 182),  # Amethyst Purple
            (241, 196, 15),  # Sun Yellow
            (230, 126, 34),  # Carrot Orange
            (231, 76, 60),   # Alizarin Red
            (26, 188, 156),  # Turquoise
            (243, 156, 18),  # Orange
        ]

        if results and len(results) > 0:
            boxes = results[0].boxes
            for box in boxes:
                cls_id = int(box.cls[0].item())
                cls_name = self.model.names.get(cls_id, f"class_{cls_id}")
                conf_score = round(float(box.conf[0].item()), 4)

                xyxy = box.xyxy[0].tolist()
                x1, y1, x2, y2 = xyxy[0], xyxy[1], xyxy[2], xyxy[3]
                bw = round(x2 - x1, 2)
                bh = round(y2 - y1, 2)

                # Store detection record
                detection = DetectedItem(
                    class_id=cls_id,
                    class_name=cls_name,
                    confidence=conf_score,
                    bbox=BoundingBox(
                        x1=round(x1, 2),
                        y1=round(y1, 2),
                        x2=round(x2, 2),
                        y2=round(y2, 2),
                        width=bw,
                        height=bh,
                    ),
                )
                detections.append(detection)

                # Aggregate class tally
                class_counts[cls_name] = class_counts.get(cls_name, 0) + 1

                # Draw bounding box & high-visibility label
                color = palette[cls_id % len(palette)]
                ix1, iy1, ix2, iy2 = int(x1), int(y1), int(x2), int(y2)
                cv2.rectangle(annotated_img, (ix1, iy1), (ix2, iy2), color, 2)

                label = f"{cls_name} {int(conf_score * 100)}%"
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.5
                thickness = 1
                (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, thickness)

                # Ensure label box stays inside image boundary
                label_y1 = max(0, iy1 - text_h - 6)
                label_y2 = max(text_h + 6, iy1)
                cv2.rectangle(
                    annotated_img,
                    (ix1, label_y1),
                    (ix1 + text_w + 6, label_y2),
                    color,
                    -1,
                )
                cv2.putText(
                    annotated_img,
                    label,
                    (ix1 + 3, label_y2 - 4),
                    font,
                    font_scale,
                    (255, 255, 255),
                    thickness,
                    cv2.LINE_AA,
                )

        # Save annotated image safely
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        safe_base_name = Path(filename).stem.replace(" ", "_")
        annotated_filename = f"{timestamp_str}_{safe_base_name}_annotated.jpg"
        
        output_dir = Path(settings.DETECTION_RESULTS_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        saved_file_path = output_dir / annotated_filename

        cv2.imwrite(str(saved_file_path), annotated_img, [cv2.IMWRITE_JPEG_QUALITY, 92])

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Build public web-accessible URL
        annotated_image_url = f"/static/detections/{annotated_filename}"

        return ShelfDetectionResponse(
            filename=filename,
            image_width=width,
            image_height=height,
            total_detected=len(detections),
            class_counts=class_counts,
            detections=detections,
            annotated_image_url=annotated_image_url,
            annotated_image_path=str(saved_file_path).replace("\\", "/"),
            model_name=str(Path(self.model_path).name),
            model_mode=self._model_mode,
            inference_time_ms=elapsed_ms,
        )
    def detect_from_array(self, frame_rgb: "np.ndarray") -> Dict:
        """
        Run YOLO inference on a pre-loaded RGB numpy array (e.g. from a CCTV frame).

        Args:
            frame_rgb: H×W×3 numpy array in RGB channel order.

        Returns:
            Dict with keys: detections, counts_per_class, total_detected,
            annotated_image_array (BGR numpy array), model_mode.
        """
        conf = settings.YOLO_CONFIDENCE_THRESHOLD
        # YOLO accepts both RGB and BGR arrays; ultralytics handles conversion
        results = self.model.predict(source=frame_rgb, conf=conf, verbose=False)

        detections = []
        class_counts: Dict[str, int] = {}

        # BGR copy for annotation
        annotated = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

        palette = [
            (46, 204, 113), (52, 152, 219), (155, 89, 182),
            (241, 196, 15), (230, 126, 34), (231, 76, 60),
        ]

        if results and len(results) > 0:
            for box in results[0].boxes:
                cls_id   = int(box.cls[0].item())
                cls_name = self.model.names.get(cls_id, f"class_{cls_id}")
                conf_v   = round(float(box.conf[0].item()), 4)
                x1, y1, x2, y2 = box.xyxy[0].tolist()

                detections.append({
                    "class_name": cls_name,
                    "confidence": conf_v,
                    "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                })
                class_counts[cls_name] = class_counts.get(cls_name, 0) + 1

                color = palette[cls_id % len(palette)]
                cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                cv2.putText(
                    annotated, f"{cls_name} {int(conf_v*100)}%",
                    (int(x1) + 2, max(0, int(y1) - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA,
                )

        return {
            "detections":          detections,
            "counts_per_class":    class_counts,
            "total_detected":      len(detections),
            "annotated_image_array": annotated,
            "model_mode":          self._model_mode,
        }


# Global singleton instance
vision_service = VisionService()
