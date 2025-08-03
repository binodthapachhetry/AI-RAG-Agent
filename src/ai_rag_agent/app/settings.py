from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", extra="ignore")

    name: str = "ai-rag-agent"
    version: str = "0.1.0"
    debug: bool = True

    enable_tracing: bool = False
    otel_endpoint: str | None = None


settings = Settings()
