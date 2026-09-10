"""Application configuration, read from environment variables."""
import logging
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("doener.config")

_DEV_FALLBACK_SECRET = "insecure-dev-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str = "sqlite:///./doener_dev.db"

    # JWT
    JWT_SECRET_KEY: str = _DEV_FALLBACK_SECRET
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 14  # 2 weeks (no refresh token)

    # CORS
    CORS_ORIGINS: str = ""

    # Server
    PORT: int = 8000

    @property
    def cors_origins_list(self) -> list[str]:
        if not self.CORS_ORIGINS:
            return []
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.JWT_SECRET_KEY == _DEV_FALLBACK_SECRET:
        logger.warning(
            "JWT_SECRET_KEY is not set — using an INSECURE development fallback. "
            "Set JWT_SECRET_KEY in the environment before deploying to production."
        )
    return settings


settings = get_settings()
