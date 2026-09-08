"""Runtime configuration for VoxShield.

Configuration is deliberately environment based so development defaults cannot
silently become production policy.
"""

import os
from dataclasses import dataclass


def _csv_env(name: str, default: str) -> list[str]:
    return [value.strip() for value in os.getenv(name, default).split(",") if value.strip()]


@dataclass(frozen=True)
class Settings:
    environment: str
    allowed_origins: list[str]
    max_upload_bytes: int
    rate_limit_per_minute: int
    voiceprint_retention_days: int
    admin_token: str | None
    enable_cloud_tts: bool
    tts_timeout_seconds: int


settings = Settings(
    environment=os.getenv("VOXSHIELD_ENV", "development").lower(),
    # Set VOXSHIELD_ALLOWED_ORIGINS to the exact HTTPS frontend origins in production.
    allowed_origins=_csv_env("VOXSHIELD_ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000"),
    max_upload_bytes=int(os.getenv("VOXSHIELD_MAX_UPLOAD_BYTES", str(50 * 1024 * 1024))),
    rate_limit_per_minute=int(os.getenv("VOXSHIELD_RATE_LIMIT_PER_MINUTE", "30")),
    voiceprint_retention_days=int(os.getenv("VOXSHIELD_VOICEPRINT_RETENTION_DAYS", "30")),
    admin_token=os.getenv("VOXSHIELD_ADMIN_TOKEN") or None,
    enable_cloud_tts=os.getenv("VOXSHIELD_ENABLE_CLOUD_TTS", "true").lower() == "true",
    tts_timeout_seconds=int(os.getenv("VOXSHIELD_TTS_TIMEOUT_SECONDS", "12")),
)

