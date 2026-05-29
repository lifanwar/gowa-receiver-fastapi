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

    # Redis Pub/Sub channel prefix.
    # Final channel format: {pubsub_channel_prefix}:{device_id}
    pubsub_channel_prefix: str = "wa:incoming"

    # Optional whitelist. Empty means all devices are accepted.
    # Example: ALLOWED_DEVICES=device_1,device_2,6281234567890
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
