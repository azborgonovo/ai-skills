import os

DEFAULT_MAX_ATTEMPTS = 3


def max_attempts() -> int:
    """Attempts per delivery, including the first one."""
    return int(os.environ.get("ORDERS_RETRY_MAX_ATTEMPTS", DEFAULT_MAX_ATTEMPTS))


def backoff_seconds(attempt: int) -> float:
    return min(2.0 ** attempt, 60.0)
