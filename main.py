import json

from fastapi import FastAPI, Header, HTTPException, Request

from normalizer import normalize_gowa_payload, safe_key
from redis_pubsub import (
    get_channel_name,
    ping_redis,
    publish_event,
)
from settings import get_settings
from signature import verify_gowa_signature


settings = get_settings()

app = FastAPI(title=settings.app_name)


@app.get("/health")
async def health_check():
    redis_ok = await ping_redis()

    return {
        "ok": True,
        "redis": redis_ok,
        "transport": "redis_pubsub",
        "channel_prefix": settings.pubsub_channel_prefix,
    }


@app.post("/webhooks/gowa")
async def receive_gowa_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(
        default=None,
        alias="X-Hub-Signature-256",
    ),
):
    raw_body = await request.body()

    if not verify_gowa_signature(
        raw_body=raw_body,
        signature_header=x_hub_signature_256,
        secret=settings.gowa_webhook_secret,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook signature",
        )

    try:
        parsed_body = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload",
        ) from exc

    try:
        data = normalize_gowa_payload(parsed_body)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    device_id = safe_key(data["device_id"])

    allowed_devices = settings.allowed_device_set
    if allowed_devices and device_id not in allowed_devices:
        return {
            "ok": True,
            "published": False,
            "reason": "device_not_allowed",
            "event": data["event"],
            "device_id": device_id,
        }

    channel_name = get_channel_name(device_id)

    try:
        subscribers = await publish_event(
            channel_name=channel_name,
            data=data,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Failed to publish event to Redis Pub/Sub",
        ) from exc

    return {
        "ok": True,
        "published": True,
        "event": data["event"],
        "device_id": device_id,
        "channel": channel_name,
        "subscribers": subscribers,
    }
