from common.auth import create_token
from common.db import cursor_ctx, execute, fetch_one
from common.response import fail, success
from common.utils import gen_numeric_code, hash_code, parse_event, utc_now, validate_phone


def _verify_sms_code(cursor, phone: str, purpose: str, code: str, now):
    row = fetch_one(
        cursor,
        """
        SELECT id, code_hash, expires_at, used
        FROM verification_codes
        WHERE phone = %s AND purpose = %s
        ORDER BY id DESC
        LIMIT 1
        """,
        (phone, purpose),
    )
    if not row:
        return False, "验证码不存在"
    if row["used"] == 1:
        return False, "验证码已失效"
    if row["expires_at"] < now:
        return False, "验证码已过期"
    expected_hash = hash_code(phone, code, purpose)
    if row["code_hash"] != expected_hash:
        return False, "验证码错误"

    execute(
        cursor,
        "UPDATE verification_codes SET used = 1, used_at = %s WHERE id = %s",
        (now, row["id"]),
    )
    return True, None


def _upsert_elder(cursor, phone: str, elder_name: str, now):
    execute(
        cursor,
        """
        INSERT INTO users (role, phone, name, created_at, updated_at, last_operation_at)
        VALUES ('elder', %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            updated_at = VALUES(updated_at),
            role = 'elder'
        """,
        (phone, elder_name, now, now, now),
    )
    return fetch_one(
        cursor,
        "SELECT id, role, phone, name FROM users WHERE role = 'elder' AND phone = %s LIMIT 1",
        (phone,),
    )


def _create_binding_code(cursor, elder_id: int, elder_phone: str, now):
    code = gen_numeric_code(6)
    code_hash = hash_code(elder_phone, code, "bind")
    execute(
        cursor,
        """
        UPDATE binding_codes
        SET used = 1, used_at = %s
        WHERE elder_id = %s AND used = 0
        """,
        (now, elder_id),
    )
    execute(
        cursor,
        """
        INSERT INTO binding_codes (elder_id, code_hash, expires_at, created_at, used)
        VALUES (%s, %s, DATE_ADD(%s, INTERVAL 5 MINUTE), %s, 0)
        """,
        (elder_id, code_hash, now, now),
    )
    return code


def _child_bind(
    cursor,
    elder_phone: str,
    binding_code: str,
    openid: str,
    nickname: str,
    child_phone: str,
    now,
):
    elder = fetch_one(
        cursor,
        "SELECT id, phone, name FROM users WHERE role = 'elder' AND phone = %s LIMIT 1",
        (elder_phone,),
    )
    if not elder:
        return None, "老人账号不存在，请先让老人登录"

    code_row = fetch_one(
        cursor,
        """
        SELECT id, code_hash, expires_at, used
        FROM binding_codes
        WHERE elder_id = %s
        ORDER BY id DESC
        LIMIT 1
        """,
        (elder["id"],),
    )
    if not code_row:
        return None, "绑定码不存在"
    if code_row["used"] == 1:
        return None, "绑定码已失效"
    if code_row["expires_at"] < now:
        return None, "绑定码已过期"
    if code_row["code_hash"] != hash_code(elder_phone, binding_code, "bind"):
        return None, "绑定码错误"

    execute(
        cursor,
        "UPDATE binding_codes SET used = 1, used_at = %s WHERE id = %s",
        (now, code_row["id"]),
    )

    execute(
        cursor,
        """
        INSERT INTO users (role, openid, name, phone, created_at, updated_at, last_operation_at)
        VALUES ('child', %s, %s, NULLIF(%s, ''), %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            phone = VALUES(phone),
            updated_at = VALUES(updated_at),
            last_operation_at = VALUES(last_operation_at)
        """,
        (openid, nickname, child_phone, now, now, now),
    )
    child = fetch_one(
        cursor,
        "SELECT id, role, openid, name FROM users WHERE role = 'child' AND openid = %s LIMIT 1",
        (openid,),
    )

    execute(
        cursor,
        """
        INSERT INTO bindings (elder_id, child_id, status, created_at, updated_at)
        VALUES (%s, %s, 'active', %s, %s)
        ON DUPLICATE KEY UPDATE
            status = 'active',
            updated_at = VALUES(updated_at)
        """,
        (elder["id"], child["id"], now, now),
    )

    return {"elder": elder, "child": child}, None


def main_handler(event, context):
    req = parse_event(event)
    if req["method"] == "OPTIONS":
        return success()
    if req["method"] != "POST":
        return fail("method not allowed", status_code=405)

    action = req["body"].get("action", "elder_login")
    now = utc_now()

    try:
        with cursor_ctx() as (_, cursor):
            if action == "elder_login":
                phone = str(req["body"].get("phone", "")).strip()
                code = str(req["body"].get("code", "")).strip()
                elder_name = str(req["body"].get("elder_name", "爸爸")).strip() or "爸爸"
                if not validate_phone(phone):
                    return fail("手机号格式不正确")
                if len(code) != 6 or not code.isdigit():
                    return fail("验证码格式不正确")

                ok, error = _verify_sms_code(cursor, phone, "elder_login", code, now)
                if not ok:
                    return fail(error)

                elder = _upsert_elder(cursor, phone, elder_name, now)
                binding_code = _create_binding_code(cursor, elder["id"], phone, now)
                token = create_token(
                    {"uid": elder["id"], "role": "elder", "phone": elder["phone"], "name": elder["name"]}
                )
                return success(
                    {
                        "token": token,
                        "user": elder,
                        "binding_code": binding_code,
                        "binding_code_expire_seconds": 300,
                    }
                )

            if action == "child_bind":
                elder_phone = str(req["body"].get("elder_phone", "")).strip()
                binding_code = str(req["body"].get("binding_code", "")).strip()
                openid = str(req["body"].get("openid", "")).strip()
                nickname = str(req["body"].get("nickname", "子女")).strip() or "子女"
                child_phone = str(req["body"].get("child_phone", "")).strip()

                if not validate_phone(elder_phone):
                    return fail("老人手机号格式不正确")
                if len(binding_code) != 6 or not binding_code.isdigit():
                    return fail("绑定码格式不正确")
                if not openid:
                    return fail("openid 不能为空")
                if child_phone and not validate_phone(child_phone):
                    return fail("子女联系电话格式不正确")

                bound, error = _child_bind(
                    cursor,
                    elder_phone,
                    binding_code,
                    openid,
                    nickname,
                    child_phone,
                    now,
                )
                if error:
                    return fail(error)

                token = create_token(
                    {
                        "uid": bound["child"]["id"],
                        "role": "child",
                        "openid": openid,
                        "elder_id": bound["elder"]["id"],
                    }
                )
                return success({"token": token, **bound})

            return fail("unsupported action")
    except Exception as exc:
        return fail(f"登录失败: {exc}", status_code=500)

