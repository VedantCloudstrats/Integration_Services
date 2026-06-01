from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_title: str = "SWMM CMMS Integration APIs"
    app_description: str = "Stateless FastAPI microservice for CMMS API validation."
    app_version: str = "2.0.0"
    debug: bool = True

    api_key: str = "dev-secret-key"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
