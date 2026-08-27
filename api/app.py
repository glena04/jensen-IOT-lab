from flask import Flask, jsonify, request, render_template
import os
import socket

from db import (
    device_exists,
    get_devices,
    get_measurements,
    get_latest_measurement,
    get_measurements_for_device,
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
    # TODO M1:
    # Läs senaste mätningen från PostgreSQL med get_latest_measurement(...).
    # Returnera 404 om sensorn eller en mätning saknas.
    #
    # TODO M2:
    # Utöka M1-lösningen med cache-aside:
    # 1. Försök läsa från Redis.
    # 2. Vid cache miss: läs från PostgreSQL.
    # 3. Spara databasresultatet i Redis.
    return jsonify({
        "message": "TODO: implementera latest measurement",
        "deviceId": device_id
    }), 501


@app.get("/devices/<device_id>/measurements")
def device_history(device_id):
    # TODO M1:
    # Hämta sensorhistorik från PostgreSQL.
    # Känd sensor utan mätningar: 200 och []. Okänd sensor: 404.
    return jsonify({
        "message": "TODO: implementera device history",
        "deviceId": device_id
    }), 501


@app.post("/measurements")
def create_measurement():
    data = request.get_json(silent=True) or {}
    errors = validate_measurement(data)
 
    if errors:
        print(f"INVALID measurement from {data.get('deviceId', 'unknown')}: {errors}")
        return jsonify({"errors": errors}), 400
 
    device_id = data["deviceId"]
 
    # M1: an unknown deviceId is a client error, not a database error.
    if not device_exists(device_id):
        print(f"UNKNOWN device rejected: {device_id}")
        return jsonify({"errors": [f"unknown deviceId: {device_id}"]}), 400
 
    saved = insert_measurement(data)
 
    # M2: keep the latest-cache in sync with the newest write.
    set_latest_in_cache(device_id, saved)
 
    print(f"STORED measurement: {saved}")
    return jsonify({"status": "created", "measurement": saved}), 201

@app.get("/statistics")
def statistics():
    # ⭐ Utmaning:
    # Returnera antal devices, antal measurements, avg temp etc.
    return jsonify({"message": "Optional challenge"}), 501


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
