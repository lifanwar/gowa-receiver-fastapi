import hashlib
import hmac


def normalize_signature(signature: str | None) -> str | None:
    if not signature:
        return None

    signature = signature.strip()

    if signature.startswith("sha256="):
        return signature.replace("sha256=", "", 1)

    return signature


def verify_gowa_signature(
    raw_body: bytes,
    signature_header: str | None,
    secret: str,
) -> bool:
    """
    Jika secret kosong, validasi signature dilewati.
    Untuk production, selalu isi GOWA_WEBHOOK_SECRET.
    """
    if not secret:
        return True

    received_signature = normalize_signature(signature_header)

    if not received_signature:
        return False

    expected_signature = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected_signature, received_signature)