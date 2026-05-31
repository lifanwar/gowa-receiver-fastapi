import json
import hashlib

import redis.asyncio as redis

from settings import get_settings


settings = get_settings()

redis_conn = redis.from_url(
    settings.redis_url,
    decode_responses=True,
)

async def ping_redis() -> bool:
    return bool(await redis_conn.ping())

def get_channel_name(device_id: str) -> str:
    return f"{settings.pubsub_channel_prefix}:{device_id}"

async def publish_event(
    channel_name: str,
    data: dict,
) -> int:
    subscribers = await redis_conn.publish(
        channel_name,
        json.dumps(data, ensure_ascii=False),
    )

    return int(subscribers)

def get_dedup_key(event_id: str) -> str:
    hashed = hashlib.sha256(event_id.encode("utf-8")).hexdigest()[:32]
    return f"{settings.dedup_prefix}:{hashed}"


async def publish_event_once(
    channel_name: str,
    data: dict,
    event_id: str,
) -> dict:
    dedup_key = get_dedup_key(event_id)

    is_new = await redis_conn.set(
        dedup_key,
        "1",
        ex=settings.dedup_ttl_seconds,
        nx=True,
    )

    if not is_new:
        return {
            "published": False,
            "duplicate": True,
            "subscribers": 0,
        }

    subscribers = await publish_event(
        channel_name=channel_name,
        data=data,
    )

    return {
        "published": True,
        "duplicate": False,
        "subscribers": subscribers,
    }