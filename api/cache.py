from flask import Flask, jsonify, request, render_template
import os
import socket

from db import (
    device_exists,
    get_devices,
    get_measurements,
    get_latest_measurement,
    get_measurements_for_device,
    get_statistics,
    insert_measurement,
)
from validation import validate_measurement
from cache import get_latest_from_cache, set_latest_in_cache

app = Flask(__name__)

APP_VERSION = os.getenv("APP_VERSION", "v1")
POD_NAME = socket.gethostname()


@app.get("/")
def dashboard():
    return render_template("index.html", version=APP_VERSION, pod=POD_NAME)


@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "version": APP_VERSION,
        "pod": POD_NAME,
    }), 200


@app.get("/devices")
def devices():
    return jsonify(get_devices()), 200


@app.get("/measurements")
def measurements():
    return jsonify(get_measurements()), 200


@app.get("/devices/<device_id>/latest")
def latest(device_id):
    # M2: cache-aside. 1) Läs från Redis. 2) Vid cache miss: läs från PostgreSQL. 3) Spara tillbaka.
    cached = get_latest_from_cache(device_id)
    if cached is not None:
        return jsonify({**cached, "source": "cache"}), 200

    # M1: Okänd sensor samt känd sensor utan mätningar ger båda 404,
    # men med olika felmeddelanden så att orsaken syns tydligt.
    if not device_exists(device_id):
        return jsonify({"error": f"Unknown device: {device_id}"}), 404

    measurement = get_latest_measurement(device_id)
    if measurement is None:
        return jsonify({"error": f"No measurements for device: {device_id}"}), 404

    set_latest_in_cache(device_id, measurement)
    return jsonify({**measurement, "source": "database"}), 200


@app.get("/devices/<device_id>/measurements")
def device_history(device_id):
    # M1: Känd sensor utan mätningar -> 200 och []. Okänd sensor -> 404.
    if not device_exists(device_id):
        return jsonify({"error": f"Unknown device: {device_id}"}), 404

    return jsonify(get_measurements_for_device(device_id)), 200


@app.post("/measurements")
def create_measurement():
    data = request.get_json(silent=True) or {}
    errors = validate_measurement(data)

    if errors:
        print(f"INVALID measurement from {data.get('deviceId', 'unknown')}: {errors}")
        return jsonify({"errors": errors}), 400

    device_id = data["deviceId"]

    # M1: Ett okänt deviceId är ett klientfel, inte ett databasfel.
    if not device_exists(device_id):
        print(f"UNKNOWN device rejected: {device_id}")
        return jsonify({"errors": [f"unknown deviceId: {device_id}"]}), 400

    saved = insert_measurement(data)

    # M2: Håll cachen synkroniserad med den senaste skrivningen.
    set_latest_in_cache(device_id, saved)

    print(f"STORED measurement: {saved}")
    return jsonify({"status": "created", "measurement": saved}), 201


@app.get("/statistics")
def statistics():
    # Frivillig fördjupning: aggregerad statistik över sensorer och mätningar.
    return jsonify(get_statistics()), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
