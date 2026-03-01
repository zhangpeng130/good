from datetime import timedelta

from common.auth import AuthError, require_auth
from common.db import cursor_ctx, execute, fetch_all, fetch_one
from common.response import fail, success
from common.tencent_clients import send_wechat_subscription
from common.utils import parse_event, utc_now


def _safe_int(value):
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_float(value):
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _get_dashboard(cursor, elder_id: int):
    elder = fetch_one(
        cursor,
        """
        SELECT
            id, name, phone, last_heartbeat_at, last_operation_at,
            (SELECT battery_level FROM heartbeats h WHERE h.elder_id = users.id ORDER BY h.id DESC LIMIT 1) AS latest_battery,
            (SELECT created_at FROM heartbeats h WHERE h.elder_id = users.id AND h.event_type = 'checkin' ORDER BY h.id DESC LIMIT 1) AS last_checkin_at
        FROM users
        WHERE id = %s AND role = 'elder'
        LIMIT 1
        """,
        (elder_id,),
    )
    if not elder:
        return None

    now = utc_now()
    online = False
    if elder["last_heartbeat_at"] is not None:
        online = now - elder["last_heartbeat_at"] <= timedelta(minutes=10)

    sos_list = fetch_all(
        cursor,
        """
        SELECT id, audio_url, latitude, longitude, address, created_at
        FROM sos_events
        WHERE elder_id = %s
        ORDER BY id DESC
        LIMIT 20
        """,
        (elder_id,),
    )

    return {
        "status": "online" if online else "offline",
        "elder": elder,
        "recent_sos": sos_list,
    }


def _handle_elder_event(cursor, elder_id: int, action: str, body: dict, now):
    battery_level = _safe_int(body.get("battery_level"))
    app_active = bool(body.get("app_active", False))
    location = body.get("location", {}) or {}
    lat = _safe_float(location.get("latitude", body.get("latitude")))
    lng = _safe_float(location.get("longitude", body.get("longitude")))

    execute(
        cursor,
        """
        INSERT INTO heartbeats (elder_id, event_type, battery_level, latitude, longitude, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (elder_id, action, battery_level, lat, lng, now),
    )

    if action == "checkin" or app_active:
        execute(
            cursor,
            """
            UPDATE users
            SET last_heartbeat_at = %s, last_operation_at = %s, updated_at = %s
            WHERE id = %s AND role = 'elder'
            """,
            (now, now, now, elder_id),
        )
    else:
        execute(
            cursor,
            """
            UPDATE users
            SET last_heartbeat_at = %s, updated_at = %s
            WHERE id = %s AND role = 'elder'
            """,
            (now, now, elder_id),
        )

    if action == "checkin":
        elder = fetch_one(
            cursor,
            "SELECT id, name FROM users WHERE id = %s AND role = 'elder' LIMIT 1",
            (elder_id,),
        )
        contacts = fetch_all(
            cursor,
            """
            SELECT c.openid
            FROM bindings b
            JOIN users c ON c.id = b.child_id
            WHERE b.elder_id = %s AND b.status = 'active'
            """,
            (elder_id,),
        )
        openids = [item["openid"] for item in contacts if item.get("openid")]
        send_wechat_subscription(
            openids,
            "我很好",
            f"{elder['name']} 说：我很好！",
        )

    return {"event": action, "updated_at": now.isoformat()}


def _handle_child_event(cursor, claims: dict, action: str, body: dict, now):
    child_id = int(claims["uid"])
    elder_id = int(body.get("elder_id") or claims.get("elder_id") or 0)
    if elder_id <= 0:
        return None, "缺少 elder_id"

    binding = fetch_one(
        cursor,
        """
        SELECT id, status FROM bindings
        WHERE elder_id = %s AND child_id = %s
        LIMIT 1
        """,
        (elder_id, child_id),
    )
    if not binding or binding["status"] != "active":
        return None, "绑定关系不存在"

    if action == "unbind":
        execute(
            cursor,
            "UPDATE bindings SET status = 'inactive', updated_at = %s WHERE id = %s",
            (now, binding["id"]),
        )
        return {"unbind": True}, None

    dashboard = _get_dashboard(cursor, elder_id)
    return dashboard, None


def main_handler(event, context):
    req = parse_event(event)
    if req["method"] == "OPTIONS":
        return success()
    if req["method"] != "POST":
        return fail("method not allowed", status_code=405)

    try:
        claims = require_auth(req["headers"], roles={"elder", "child"})
    except AuthError as exc:
        return fail(str(exc), status_code=401)

    action = str(req["body"].get("action", "heartbeat")).strip()
    now = utc_now()

    try:
        with cursor_ctx() as (_, cursor):
            if claims["role"] == "elder":
                elder_action = action if action in {"heartbeat", "checkin"} else "heartbeat"
                data = _handle_elder_event(cursor, int(claims["uid"]), elder_action, req["body"], now)
                return success(data)

            # child
            child_action = action if action in {"get_dashboard", "unbind"} else "get_dashboard"
            data, error = _handle_child_event(cursor, claims, child_action, req["body"], now)
            if error:
                return fail(error, status_code=404)
            return success(data)
    except Exception as exc:
        return fail(f"heartbeat处理失败: {exc}", status_code=500)

