import json

from fastapi import FastAPI, Header, HTTPException, Request

from normalizer import build_event_id, normalize_gowa_payload, safe_key
from redis_stream import (
    get_stream_name,
    is_duplicate_event,
    ping_redis,
    publish_event,
    release_dedup_event,
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
        "stream_maxlen": settings.stream_maxlen,
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
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload",
        )

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
            "queued": False,
            "reason": "device_not_allowed",
            "device_id": device_id,
        }

    event_id = build_event_id(data, raw_body)

    duplicate = await is_duplicate_event(event_id)
    if duplicate:
        return {
            "ok": True,
            "queued": False,
            "duplicate": True,
            "event_id": event_id,
            "event": data["event"],
            "device_id": device_id,
        }

    stream_name = get_stream_name(device_id)

    try:
        redis_stream_id = await publish_event(
            stream_name=stream_name,
            event_id=event_id,
            data=data,
        )
    except Exception:
        await release_dedup_event(event_id)
        raise

    return {
        "ok": True,
        "queued": True,
        "event_id": event_id,
        "redis_stream_id": redis_stream_id,
        "event": data["event"],
        "device_id": device_id,
        "stream": stream_name,
    }