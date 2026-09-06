from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app import security
from app.config import Settings


def test_normalize_phone_number_accepts_readable_input():
    assert security.normalize_phone_number("+91 98765-43210") == "+919876543210"


@pytest.mark.parametrize("value", ["abc", "+12+34", "123", "1" * 16])
def test_normalize_phone_number_rejects_invalid_input(value):
    with pytest.raises(ValueError):
        security.normalize_phone_number(value)


def test_rate_limit_rejects_excess_requests(monkeypatch):
    monkeypatch.setattr(
        security,
        "settings",
        Settings("test", [], 1024, 1, 1, None),
    )
    request = SimpleNamespace(client=SimpleNamespace(host="test-client"))
    security.enforce_rate_limit(request, "test")
    with pytest.raises(HTTPException) as error:
        security.enforce_rate_limit(request, "test")
    assert error.value.status_code == 429
