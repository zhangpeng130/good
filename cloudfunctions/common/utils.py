import base64
import hashlib
import json
import re
import secrets
from datetime import datetime, timezone
from typing import Any, Dict


PHONE_REGEX = re.compile(r"^1[3-9]\d{9}$")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_event(event: Dict[str, Any]) -> Dict[str, Any]:
    raw_body = event.get("body")
    if raw_body is None:
        body_text = ""
    elif event.get("isBase64Encoded"):
        body_text = base64.b64decode(raw_body).decode("utf-8")
    else:
        body_text = raw_body if isinstance(raw_body, str) else json.dumps(raw_body)

    try:
        body_json = json.loads(body_text) if body_text else {}
    except json.JSONDecodeError:
        body_json = {}

    headers = event.get("headers") or {}
    normalized_headers = {str(k).lower(): v for k, v in headers.items()}

    return {
        "method": (event.get("httpMethod") or "POST").upper(),
        "path": event.get("path", "/"),
        "headers": normalized_headers,
        "query": event.get("queryString") or event.get("queryStringParameters") or {},
        "body": body_json,
        "raw_body": body_text,
    }


def validate_phone(phone: str) -> bool:
    return bool(PHONE_REGEX.match(phone))


def gen_numeric_code(length: int = 6) -> str:
    return "".join(secrets.choice("0123456789") for _ in range(length))


def hash_code(phone: str, code: str, purpose: str) -> str:
    plain = f"{phone}:{purpose}:{code}"
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()


def decode_b64_data(data: str) -> bytes:
    if "," in data and data.split(",", 1)[0].startswith("data:"):
        data = data.split(",", 1)[1]
    return base64.b64decode(data)

