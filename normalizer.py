import hashlib
import re
from typing import Any


def safe_key(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.@-]", "_", value.strip())
    return cleaned[:250]


def detect_media(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Deteksi media berdasarkan field yang dikirim GOWA.
    Contoh payload Anda memakai field: image.
    Fungsi ini tetap disiapkan untuk media lain jika nanti dipakai.
    """
    media_fields = ["image", "video", "audio", "document", "sticker"]

    for media_type in media_fields:
        media_path = payload.get(media_type)

        if media_path:
            return {
                "media_type": media_type,
                "media_path": str(media_path),
            }

    return {
        "media_type": None,
        "media_path": None,
    }


def normalize_gowa_payload(parsed_body: dict[str, Any]) -> dict[str, Any]:
    """
    Normalizer khusus untuk payload webhook GOWA
    """

    payload = parsed_body.get("payload")

    if not isinstance(payload, dict):
        raise ValueError("payload not found or invalid in webhook body")

    device_id = parsed_body.get("device_id")
    event = parsed_body.get("event", "message")

    if not device_id:
        raise ValueError("device_id not found in webhook payload")

    message_id = payload.get("id")
    chat_id = payload.get("chat_id")
    sender = payload.get("from")
    is_from_me = bool(payload.get("is_from_me", False))

    media = detect_media(payload)

    return {
        "event": str(event),
        "device_id": str(device_id),

        "message_id": str(message_id) if message_id else None,

        # chat_id adalah ID percakapan/kontak tujuan.
        # Untuk pesan keluar, ini biasanya nomor customer.
        "chat_id": str(chat_id) if chat_id else None,
        "chat_lid": str(payload.get("chat_lid")) if payload.get("chat_lid") else None,

        # sender adalah pengirim aktual dari payload.
        # Untuk pesan keluar, sender biasanya device_id sendiri.
        "sender": str(sender) if sender else None,
        "sender_lid": str(payload.get("from_lid")) if payload.get("from_lid") else None,
        "sender_name": str(payload.get("from_name")) if payload.get("from_name") else None,

        # contact_id dibuat agar lebih mudah mengambil lawan bicara/customer.
        "contact_id": str(chat_id) if chat_id else None,

        "text": str(payload.get("body") or ""),
        "is_group": str(chat_id or "").endswith("@g.us"),
        "is_from_me": is_from_me,
        "direction": "outgoing" if is_from_me else "incoming",

        "replied_to_id": (
            str(payload.get("replied_to_id"))
            if payload.get("replied_to_id")
            else None
        ),

        "timestamp": (
            str(payload.get("timestamp"))
            if payload.get("timestamp")
            else None
        ),

        "media_type": media["media_type"],
        "media_path": media["media_path"],

        "raw": parsed_body,
    }


def build_event_id(data: dict[str, Any], raw_body: bytes) -> str:
    event = data.get("event") or "unknown"
    device_id = data.get("device_id") or "unknown"

    payload_id = (
        data.get("message_id")
        or hashlib.sha256(raw_body).hexdigest()[:32]
    )

    return safe_key(f"{device_id}_{event}_{payload_id}")