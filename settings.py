from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "gowa-webhook-api"
    redis_url: str = "redis://localhost:6379/0"

    gowa_webhook_secret: str = ""

    stream_prefix: str = "wa:incoming"
    stream_maxlen: int = 1000

    dedup_prefix: str = "wa:dedup"
    dedup_ttl_seconds: int = 86400

    allowed_devices: str = ""

    @property
    def allowed_device_set(self) -> set[str]:
        if not self.allowed_devices.strip():
            return set()

        return {
            item.strip()
            for item in self.allowed_devices.split(",")
            if item.strip()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()