import pytest

from common.auth import AuthError, create_token, require_auth


def test_require_auth_should_decode_valid_token():
    token = create_token({"uid": 100, "role": "elder"})
    claims = require_auth({"authorization": f"Bearer {token}"}, roles={"elder"})
    assert claims["uid"] == 100
    assert claims["role"] == "elder"


def test_require_auth_should_reject_missing_token():
    with pytest.raises(AuthError):
        require_auth({}, roles={"elder"})


def test_require_auth_should_reject_wrong_role():
    token = create_token({"uid": 101, "role": "child"})
    with pytest.raises(AuthError):
        require_auth({"authorization": f"Bearer {token}"}, roles={"elder"})

