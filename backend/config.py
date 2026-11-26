from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json


class Settings(BaseSettings):
    PROJECT_NAME: str = "RetailMind AI"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "dev_secret_key_change_in_production_9f83a8b271c4"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./retailmind.db"
    SYNC_DATABASE_URL: str = "sqlite:///./retailmind.db"

    # Server & CORS
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Computer Vision & YOLO Configuration
    YOLO_MODEL_PATH: str = "yolov8n.pt"  # Can point to a custom retail weights file e.g. "backend/ml_weights/retail_sku_best.pt"
    YOLO_CONFIDENCE_THRESHOLD: float = 0.25
    DETECTION_RESULTS_DIR: str = "results/detections"
    MAX_UPLOAD_SIZE_MB: int = 15
    ALLOWED_IMAGE_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, tuple)):
            return list(v)
        return []

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
