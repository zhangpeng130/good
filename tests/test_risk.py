from datetime import datetime, timedelta, timezone

from common.risk import ElderRiskSnapshot, evaluate_risks


def test_low_battery_and_stale_heartbeat_should_alert():
    now = datetime.now(timezone.utc)
    snapshot = ElderRiskSnapshot(
        elder_id=1,
        elder_name="爸爸",
        last_heartbeat_at=now - timedelta(hours=5),
        last_operation_at=now - timedelta(hours=2),
        latest_battery=8,
    )
    alerts = evaluate_risks(snapshot, now=now)
    assert any(item["type"] == "offline_low_battery" for item in alerts)


def test_prolonged_inactive_should_alert():
    now = datetime.now(timezone.utc)
    snapshot = ElderRiskSnapshot(
        elder_id=2,
        elder_name="妈妈",
        last_heartbeat_at=now - timedelta(minutes=20),
        last_operation_at=now - timedelta(hours=13),
        latest_battery=50,
    )
    alerts = evaluate_risks(snapshot, now=now)
    assert any(item["type"] == "prolonged_inactive" for item in alerts)


def test_healthy_snapshot_should_not_alert():
    now = datetime.now(timezone.utc)
    snapshot = ElderRiskSnapshot(
        elder_id=3,
        elder_name="爷爷",
        last_heartbeat_at=now - timedelta(minutes=20),
        last_operation_at=now - timedelta(hours=1),
        latest_battery=80,
    )
    alerts = evaluate_risks(snapshot, now=now)
    assert alerts == []

