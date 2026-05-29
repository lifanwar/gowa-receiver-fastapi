import json

import redis.asyncio as redis

from settings import get_settings


settings = get_settings()

redis_conn = redis.from_url(
    settings.redis_url,
    decode_responses=True,
)


def get_stream_name(device_id: str) -> str:
    return f"{settings.stream_prefix}:{device_id}"


def get_dedup_key(event_id: str) -> str:
    return f"{settings.dedup_prefix}:{event_id}"


async def ping_redis() -> bool:
    return bool(await redis_conn.ping())


async def is_duplicate_event(event_id: str) -> bool:
    is_new = await redis_conn.set(
        get_dedup_key(event_id),
        "1",
        nx=True,
        ex=settings.dedup_ttl_seconds,
    )

    return not bool(is_new)


async def release_dedup_event(event_id: str) -> None:
    await redis_conn.delete(get_dedup_key(event_id))


async def publish_event(
    stream_name: str,
    event_id: str,
    data: dict,
) -> str:
    redis_stream_id = await redis_conn.xadd(
        name=stream_name,
        fields={
            "event_id": event_id,
            "payload": json.dumps(data, ensure_ascii=False),
        },
        maxlen=settings.stream_maxlen,
        approximate=True,
    )

    return str(redis_stream_id)