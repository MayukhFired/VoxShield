"""Small dependency-free safeguards for public endpoints.

For a multi-instance production deployment replace this in-memory limiter with
an edge/WAF or Redis-backed limiter. It is still useful for the single-process
demo deployment.
"""

from collections import defaultdict, deque
from time import monotonic

from fastapi import HTTPException, Request

from app.config import settings

_requests: dict[str, deque[float]] = defaultdict(deque)


def enforce_rate_limit(request: Request, scope: str) -> None:
    client = request.client.host if request.client else "unknown"
    key = f"{scope}:{client}"
    now = monotonic()
    window_start = now - 60
    bucket = _requests[key]
    while bucket and bucket[0] <= window_start:
        bucket.popleft()
    if len(bucket) >= settings.rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Too many requests. Please try again in a minute.")
    bucket.append(now)


def require_admin(token: str | None) -> None:
    """Guard moderation actions until real authentication is configured."""
    if not settings.admin_token:
        raise HTTPException(status_code=503, detail="Moderation is not configured on this deployment.")
    if token != settings.admin_token:
        raise HTTPException(status_code=403, detail="Administrator authorization is required.")


def normalize_phone_number(value: str) -> str:
    """Return a safely comparable phone number; callers should prefer E.164 input."""
    cleaned = "".join(char for char in value.strip() if char.isdigit() or char == "+")
    if cleaned.count("+") > 1 or ("+" in cleaned and not cleaned.startswith("+")):
        raise ValueError("Phone number has an invalid format.")
    digits = cleaned.lstrip("+")
    if not 7 <= len(digits) <= 15:
        raise ValueError("Phone number must contain 7 to 15 digits.")
    return f"+{digits}" if cleaned.startswith("+") else digits
