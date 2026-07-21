from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    environment: str = "local"
    database_url: str = "postgres://smart_app:smart_app@localhost:5432/smart_app"


@lru_cache
def get_settings() -> Settings:
    return Settings()
