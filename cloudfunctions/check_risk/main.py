from datetime import timedelta

from common.auth import AuthError, require_auth
from common.db import cursor_ctx, execute, fetch_all, fetch_one
from common.response import fail, success
from common.risk import ElderRiskSnapshot, evaluate_risks
from common.tencent_clients import send_voice_message, send_wechat_subscription
from common.utils import parse_event, utc_now


def _schedule_event(event: dict) -> bool:
    return bool(event.get("Type") == "Timer" or event.get("triggerName"))


def _alert_recently_sent(cursor, elder_id: int, alert_type: str, now) -> bool:
    row = fetch_one(
        cursor,
        """
        SELECT id
        FROM risk_alerts
        WHERE elder_id = %s AND alert_type = %s AND created_at >= %s
        ORDER BY id DESC
        LIMIT 1
        """,
        (elder_id, alert_type, now - timedelta(hours=2)),
    )
    return row is not None


def _send_alert(cursor, elder: dict, alert: dict, now):
    contacts = fetch_all(
        cursor,
        """
        SELECT c.openid, c.phone
        FROM bindings b
        JOIN users c ON c.id = b.child_id
        WHERE b.elder_id = %s AND b.status = 'active'
        """,
        (elder["id"],),
    )
    openids = [item["openid"] for item in contacts if item.get("openid")]
    send_wechat_subscription(openids, "失联风险预警", alert["message"])

    if alert["type"] == "prolonged_inactive":
        for item in contacts:
            if item.get("phone"):
                send_voice_message(item["phone"], f"请尽快联系{elder['name']}，当前已超过12小时无操作。")

    execute(
        cursor,
        """
        INSERT INTO risk_alerts (elder_id, alert_type, message, created_at)
        VALUES (%s, %s, %s, %s)
        """,
        (elder["id"], alert["type"], alert["message"], now),
    )


def main_handler(event, context):
    # Allow direct timer trigger; require JWT only for manual HTTP invocation.
    if not _schedule_event(event):
        req = parse_event(event)
        if req["method"] == "OPTIONS":
            return success()
        if req["method"] != "POST":
            return fail("method not allowed", status_code=405)
        try:
            require_auth(req["headers"], roles={"system", "ops"})
        except AuthError as exc:
            return fail(str(exc), status_code=401)

    now = utc_now()
    try:
        with cursor_ctx() as (_, cursor):
            elders = fetch_all(
                cursor,
                """
                SELECT
                    u.id, u.name, u.last_heartbeat_at, u.last_operation_at,
                    (SELECT h.battery_level FROM heartbeats h WHERE h.elder_id = u.id ORDER BY h.id DESC LIMIT 1) AS latest_battery
                FROM users u
                WHERE u.role = 'elder'
                """
            )

            sent = []
            for elder in elders:
                snapshot = ElderRiskSnapshot(
                    elder_id=elder["id"],
                    elder_name=elder["name"],
                    last_heartbeat_at=elder["last_heartbeat_at"],
                    last_operation_at=elder["last_operation_at"],
                    latest_battery=elder["latest_battery"],
                )
                alerts = evaluate_risks(snapshot, now=now)
                for alert in alerts:
                    if _alert_recently_sent(cursor, elder["id"], alert["type"], now):
                        continue
                    _send_alert(cursor, elder, alert, now)
                    sent.append({"elder_id": elder["id"], "alert_type": alert["type"]})

            return success({"checked": len(elders), "alerts_sent": sent})
    except Exception as exc:
        return fail(f"风险巡检失败: {exc}", status_code=500)

