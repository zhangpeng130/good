import json
from typing import Any, Dict, Optional


def _build(status_code: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "isBase64Encoded": False,
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json; charset=utf-8",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Authorization,Content-Type",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        },
        "body": json.dumps(payload, ensure_ascii=False),
    }


def success(data: Optional[Dict[str, Any]] = None, message: str = "ok") -> Dict[str, Any]:
    return _build(200, {"code": 0, "message": message, "data": data or {}})


def fail(
    message: str,
    status_code: int = 400,
    code: int = 1000,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return _build(status_code, {"code": code, "message": message, "data": data or {}})

