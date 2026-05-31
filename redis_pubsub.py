import json

import redis.asyncio as redis

from settings import get_settings


settings = get_settings()

redis_conn = redis.from_url(
    settings.redis_url,
    decode_responses=True,
)


def get_channel_name(device_id: str) -> str:
    return f"{settings.pubsub_channel_prefix}:{device_id}"


async def ping_redis() -> bool:
    return bool(await redis_conn.ping())


async def publish_event(
    channel_name: str,
    data: dict,
) -> int:
    subscribers = await redis_conn.publish(
        channel_name,
        json.dumps(data, ensure_ascii=False),
    )

    return int(subscribers)
