from datetime import timezone
from uuid import uuid4

from common.auth import AuthError, require_auth
from common.db import cursor_ctx, execute, fetch_all, fetch_one
from common.response import fail, success
from common.tencent_clients import (
    send_voice_message,
    send_wechat_subscription,
    upload_audio_to_cos,
)
from common.utils import decode_b64_data, parse_event, utc_now


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_audio_key(elder_id: int, ext: str, now):
    timestamp = now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"sos/{elder_id}/{timestamp}_{uuid4().hex[:10]}.{ext}"


def main_handler(event, context):
    req = parse_event(event)
    if req["method"] == "OPTIONS":
        return success()
    if req["method"] != "POST":
        return fail("method not allowed", status_code=405)

    try:
        claims = require_auth(req["headers"], roles={"elder"})
    except AuthError as exc:
        return fail(str(exc), status_code=401)

    elder_id = int(claims["uid"])
    body = req["body"]
    audio_base64 = body.get("audio_base64", "")
    audio_ext = str(body.get("audio_format", "wav")).strip().lower() or "wav"
    location = body.get("location", {}) or {}

    lat = _safe_float(location.get("latitude", body.get("latitude")))
    lng = _safe_float(location.get("longitude", body.get("longitude")))
    address = str(location.get("address", body.get("address", ""))).strip()

    now = utc_now()
    audio_key = None
    audio_url = None

    try:
        if audio_base64:
            raw_audio = decode_b64_data(audio_base64)
            audio_key = _build_audio_key(elder_id, audio_ext, now)
            audio_url = upload_audio_to_cos(raw_audio, audio_key, content_type=f"audio/{audio_ext}")
    except Exception as exc:
        return fail(f"SOS录音上传失败: {exc}", status_code=500)

    try:
        with cursor_ctx() as (_, cursor):
            elder = fetch_one(
                cursor,
                "SELECT id, name, phone FROM users WHERE id = %s AND role = 'elder' LIMIT 1",
                (elder_id,),
            )
            if not elder:
                return fail("老人账号不存在", status_code=404)

            execute(
                cursor,
                """
                INSERT INTO sos_events
                (elder_id, audio_key, audio_url, latitude, longitude, address, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (elder_id, audio_key, audio_url, lat, lng, address, now),
            )
            sos = fetch_one(cursor, "SELECT LAST_INSERT_ID() AS id")

            contacts = fetch_all(
                cursor,
                """
                SELECT c.openid, c.phone
                FROM bindings b
                JOIN users c ON c.id = b.child_id
                WHERE b.elder_id = %s AND b.status = 'active'
                """,
                (elder_id,),
            )

            message = f"【紧急呼救】{elder['name']} 触发 SOS，地址：{address or '定位中'}。"
            openids = [item["openid"] for item in contacts if item.get("openid")]
            send_wechat_subscription(openids, "SOS 紧急呼救", message)

            for item in contacts:
                if item.get("phone"):
                    send_voice_message(item["phone"], message)

            return success(
                {
                    "sos_id": sos["id"],
                    "audio_url": audio_url,
                    "location": {"latitude": lat, "longitude": lng, "address": address},
                }
            )
    except Exception as exc:
        return fail(f"SOS处理失败: {exc}", status_code=500)

