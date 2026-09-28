from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="TIK_")

    app_name: str = "tik-api"
    environment: str = "development"

    tiktok_client_key: str = ""
    tiktok_client_secret: str = ""
    tiktok_redirect_uri: str = "https://tik.topachadinhos.com.br/oauth/callback"

    anthropic_api_key: str = ""

    database_url: str = "sqlite:///./data/tik.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
