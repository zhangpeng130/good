from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, Optional

import jwt

from .config import settings


class AuthError(Exception):
    """Raised when auth token is missing or invalid."""


def create_token(payload: Dict, expire_seconds: Optional[int] = None) -> str:
    ttl = expire_seconds or settings.jwt_expire_seconds
    now = datetime.now(timezone.utc)
    body = {
        **payload,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl)).timestamp()),
    }
    return jwt.encode(body, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def _extract_token(headers: Dict[str, str]) -> str:
    auth_header = headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip()
    if auth_header:
        return auth_header.strip()
    return ""


def require_auth(event_headers: Dict[str, str], roles: Optional[Iterable[str]] = None) -> Dict:
    token = _extract_token(event_headers)
    if not token:
        raise AuthError("missing authorization token")

    try:
        payload = decode_token(token)
    except jwt.PyJWTError as exc:
        raise AuthError("invalid authorization token") from exc

    if roles:
        role = payload.get("role")
        if role not in set(roles):
            raise AuthError("insufficient role")
    return payload

