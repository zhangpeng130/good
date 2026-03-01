from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional


@dataclass
class ElderRiskSnapshot:
    elder_id: int
    elder_name: str
    last_heartbeat_at: Optional[datetime]
    last_operation_at: Optional[datetime]
    latest_battery: Optional[int]


def _to_utc(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def evaluate_risks(snapshot: ElderRiskSnapshot, now: Optional[datetime] = None) -> List[dict]:
    now = _to_utc(now) or datetime.now(timezone.utc)
    last_heartbeat = _to_utc(snapshot.last_heartbeat_at)
    last_operation = _to_utc(snapshot.last_operation_at)

    alerts = []

    no_heartbeat_or_stale = (
        last_heartbeat is None or now - last_heartbeat > timedelta(hours=4)
    )
    low_battery = snapshot.latest_battery is not None and snapshot.latest_battery < 10

    if no_heartbeat_or_stale and low_battery:
        alerts.append(
            {
                "type": "offline_low_battery",
                "severity": "high",
                "message": f"{snapshot.elder_name} 可能失联（超过4小时无心跳且电量低于10%）",
            }
        )

    prolonged_no_operation = (
        last_operation is None or now - last_operation > timedelta(hours=12)
    )
    if prolonged_no_operation:
        alerts.append(
            {
                "type": "prolonged_inactive",
                "severity": "critical",
                "message": f"{snapshot.elder_name} 超过12小时无任何操作",
            }
        )

    return alerts

