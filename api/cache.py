import json
import os
import redis

client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    decode_responses=True,
)

KEY_PREFIX = "latest:"
# The cached value is only the newest measurement, so a short TTL is fine.
# PostgreSQL stays the persistent source of truth.
TTL_SECONDS = 300


def _key(device_id):
    return f"{KEY_PREFIX}{device_id}"


def get_latest_from_cache(device_id):
    """Read the latest measurement for a sensor from Redis.

    Returns None on cache miss, on invalid content, or if Redis is unavailable.
    The caller then falls back to PostgreSQL.
    """
    try:
        value = client.get(_key(device_id))
    except redis.RedisError as exc:
        print(f"CACHE read failed for {device_id}: {exc}")
        return None

    if value is None:
        return None

    try:
        return json.loads(value)
    except (TypeError, ValueError):
        print(f"CACHE contained invalid JSON for {device_id}")
        return None


def set_latest_in_cache(device_id, measurement):
    """Store the latest measurement for a sensor in Redis.

    A failing cache write is logged but never breaks the request: the data is
    already safe in PostgreSQL.
    """
    if not measurement:
        return

    try:
        client.set(_key(device_id), json.dumps(measurement), ex=TTL_SECONDS)
    except redis.RedisError as exc:
        print(f"CACHE write failed for {device_id}: {exc}")
