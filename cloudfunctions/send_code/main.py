from datetime import timedelta

from common.config import settings
from common.db import cursor_ctx, execute
from common.response import fail, success
from common.tencent_clients import send_sms_code, synthesize_code_audio
from common.utils import gen_numeric_code, hash_code, parse_event, utc_now, validate_phone


def main_handler(event, context):
    req = parse_event(event)
    if req["method"] == "OPTIONS":
        return success()
    if req["method"] != "POST":
        return fail("method not allowed", status_code=405)

    phone = str(req["body"].get("phone", "")).strip()
    purpose = str(req["body"].get("purpose", "elder_login")).strip()
    read_aloud = bool(req["body"].get("read_aloud", False))

    if not validate_phone(phone):
        return fail("手机号格式不正确")

    code = gen_numeric_code(6)
    hashed_code = hash_code(phone, code, purpose)
    now = utc_now()
    expire_at = now + timedelta(minutes=5)

    try:
        with cursor_ctx() as (_, cursor):
            execute(
                cursor,
                """
                UPDATE verification_codes
                SET used = 1, used_at = %s
                WHERE phone = %s AND purpose = %s AND used = 0
                """,
                (now, phone, purpose),
            )
            execute(
                cursor,
                """
                INSERT INTO verification_codes
                (phone, purpose, code_hash, expires_at, created_at, used)
                VALUES (%s, %s, %s, %s, %s, 0)
                """,
                (phone, purpose, hashed_code, expire_at, now),
            )
    except Exception as exc:
        return fail(f"验证码入库失败: {exc}", status_code=500)

    try:
        send_sms_code(phone, code)
    except Exception as exc:
        return fail(f"短信发送失败: {exc}", status_code=502)

    voice_audio_base64 = None
    if read_aloud:
        try:
            voice_audio_base64 = synthesize_code_audio(code)
        except Exception as exc:
            # Do not fail login flow when TTS is down.
            print(f"[warn] cosyvoice failed: {exc}")

    payload = {
        "phone": phone,
        "purpose": purpose,
        "expires_in_seconds": 300,
        "voice_audio_base64": voice_audio_base64,
    }
    if settings.debug:
        payload["debug_code"] = code
    return success(payload)

