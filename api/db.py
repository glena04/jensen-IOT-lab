import os
from decimal import Decimal
import psycopg2
import psycopg2.extras


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "jensen_iot"),
        user=os.getenv("DB_USER", "student"),
        password=os.getenv("DB_PASSWORD", "student"),
    )


def _json_ready(row):
    if row is None:
        return None
    result = dict(row)
    for key in ("temperature", "humidity"):
        if isinstance(result.get(key), Decimal):
            result[key] = float(result[key])
    if result.get("created_at") is not None:
        result["created_at"] = result["created_at"].isoformat()
    return result


def get_devices():
    query = """
        SELECT id, device_id, location, device_type
        FROM devices
        ORDER BY device_id;
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query)
            return [dict(row) for row in cur.fetchall()]


def get_measurements():
    query = """
        SELECT id, device_id, temperature, humidity, battery, created_at
        FROM measurements
        ORDER BY created_at DESC
        LIMIT 100;
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query)
            return [_json_ready(row) for row in cur.fetchall()]


def device_exists(device_id):
    query = "SELECT 1 FROM devices WHERE device_id = %s;"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (device_id,))
            return cur.fetchone() is not None


def get_latest_measurement(device_id):
    """Return the newest measurement for one sensor, or None if it has none."""
    query = f"""
        SELECT {MEASUREMENT_COLUMNS}
        FROM measurements
        WHERE device_id = %s
        ORDER BY created_at DESC, id DESC
        LIMIT 1;
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, (device_id,))
            return _json_ready(cur.fetchone())
 
 
def get_measurements_for_device(device_id):
    """Return the full history for one sensor. An empty list is a valid result."""
    query = f"""
        SELECT {MEASUREMENT_COLUMNS}
        FROM measurements
        WHERE device_id = %s
        ORDER BY created_at DESC, id DESC
        LIMIT 100;
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, (device_id,))
            return [_json_ready(row) for row in cur.fetchall()]


def insert_measurement(data):
    query = """
        INSERT INTO measurements (device_id, temperature, humidity, battery)
        VALUES (%s, %s, %s, %s)
        RETURNING id, device_id, temperature, humidity, battery, created_at;
    """
    params = (
        data["deviceId"],
        data["temperature"],
        data.get("humidity"),
        data.get("battery"),
    )
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            return _json_ready(cur.fetchone())
