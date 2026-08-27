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


MEASUREMENT_COLUMNS = "id, device_id, temperature, humidity, battery, created_at"


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
    query = f"""
        SELECT {MEASUREMENT_COLUMNS}
        FROM measurements
        ORDER BY created_at DESC, id DESC
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
    """Store one validated measurement and return the created row as JSON-ready dict.

    JSON uses deviceId, the database column is device_id. The translation
    between the two happens here and nowhere else.
    """
    query = f"""
        INSERT INTO measurements (device_id, temperature, humidity, battery)
        VALUES (%s, %s, %s, %s)
        RETURNING {MEASUREMENT_COLUMNS};
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


def get_statistics():
    """Optional challenge: aggregated numbers for GET /statistics."""
    query = """
        SELECT
            (SELECT COUNT(*) FROM devices)                       AS device_count,
            (SELECT COUNT(*) FROM measurements)                  AS measurement_count,
            (SELECT ROUND(AVG(temperature), 2) FROM measurements) AS avg_temperature,
            (SELECT ROUND(AVG(humidity), 2) FROM measurements)    AS avg_humidity,
            (SELECT COUNT(*) FROM measurements
             WHERE created_at >= NOW() - INTERVAL '24 hours')     AS measurements_last_24h;
    """
    most_active_query = """
        SELECT device_id, COUNT(*) AS measurement_count
        FROM measurements
        GROUP BY device_id
        ORDER BY measurement_count DESC, device_id
        LIMIT 1;
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query)
            stats = dict(cur.fetchone())
            for key in ("avg_temperature", "avg_humidity"):
                if isinstance(stats.get(key), Decimal):
                    stats[key] = float(stats[key])

            cur.execute(most_active_query)
            row = cur.fetchone()
            stats["most_active_device"] = dict(row) if row else None

    return stats
