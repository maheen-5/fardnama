"""Application settings loaded from environment variables."""

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class Settings:
    """Configuration values for the FardNama backend."""

    upload_dir: Path
    max_upload_bytes: int
    cors_origins: list[str]
    app_env: str
    tesseract_cmd: Optional[str]


@lru_cache
def get_settings() -> Settings:
    """Return settings loaded from the process environment, cached for reuse."""
    app_env = os.getenv("APP_ENV", "development")
    configured_origins = os.getenv("CORS_ORIGINS")
    if configured_origins is None:
        cors_origins = ["*"] if app_env == "development" else []
    else:
        cors_origins = [
            origin.strip()
            for origin in configured_origins.split(",")
            if origin.strip()
        ]

    return Settings(
        upload_dir=Path(os.getenv("FARDNAMA_UPLOAD_DIR", "data/evidence")),
        max_upload_bytes=int(
            os.getenv("FARDNAMA_MAX_UPLOAD_BYTES", "10485760")
        ),
        cors_origins=cors_origins,
        app_env=app_env,
        tesseract_cmd=os.getenv("TESSERACT_CMD"),
    )
