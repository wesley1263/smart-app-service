from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "Smart App API"
    app_version: str = "0.0.1"
    app_description: str = "Smart App — plataforma de pré-aprendizagem adaptativa"
    debug: bool = False
    environment: str = "local"
    database_url: str = "postgres://smart_app:smart_app@localhost:5432/smart_app"

    allow_origins: list[str] = ["*"]
    allow_credentials: bool = True
    allow_methods: list[str] = ["*"]
    allow_headers: list[str] = ["*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
