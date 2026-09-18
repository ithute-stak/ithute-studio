from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

DEFAULT_DATABASE_URL = (
    "postgresql+asyncpg://ithute_studio:ithute_studio@postgres:5432/ithute_studio"
)


class Settings(BaseSettings):
    app_name: str = "Ithute Document Studio API"
    environment: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = DEFAULT_DATABASE_URL
    cors_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_prefix="ITHUTE_STUDIO_",
        env_file=".env",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @model_validator(mode="after")
    def validate_production_settings(self):
        if self.environment.lower() != "production":
            return self

        try:
            database = make_url(self.database_url)
        except Exception as exc:
            raise ValueError(
                "ITHUTE_STUDIO_DATABASE_URL must be a valid SQLAlchemy database URL"
            ) from exc

        if not database.username or not database.password:
            raise ValueError(
                "ITHUTE_STUDIO_DATABASE_URL must include explicit production credentials"
            )
        if self.database_url == DEFAULT_DATABASE_URL:
            raise ValueError(
                "ITHUTE_STUDIO_DATABASE_URL must not use the default development credentials"
            )
        if not self.cors_origin_list or "*" in self.cors_origin_list:
            raise ValueError(
                "ITHUTE_STUDIO_CORS_ORIGINS must contain explicit production origins"
            )
        if any(not origin.startswith("https://") for origin in self.cors_origin_list):
            raise ValueError("Production CORS origins must use HTTPS")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
