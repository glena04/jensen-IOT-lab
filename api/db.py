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
    # TODO M1:
    # Implementera senaste mätvärdet för en sensor.
    return None


def get_measurements_for_device(device_id):
    # TODO M1:
    # Implementera historik för en sensor.
    return []


def insert_measurement(data):
    # TODO M1:
    # Spara ett validerat mätvärde i PostgreSQL.
    return None
