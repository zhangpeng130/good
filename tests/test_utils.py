import base64
import json

from common.utils import hash_code, parse_event


def test_hash_code_is_stable():
    first = hash_code("13800138000", "123456", "elder_login")
    second = hash_code("13800138000", "123456", "elder_login")
    assert first == second
    assert len(first) == 64


def test_parse_event_supports_base64_body():
    body = {"phone": "13800138000"}
    raw = base64.b64encode(json.dumps(body).encode("utf-8")).decode("utf-8")
    event = {
        "body": raw,
        "isBase64Encoded": True,
        "httpMethod": "POST",
        "headers": {"Authorization": "Bearer x"},
    }
    parsed = parse_event(event)
    assert parsed["body"]["phone"] == "13800138000"
    assert parsed["headers"]["authorization"] == "Bearer x"

