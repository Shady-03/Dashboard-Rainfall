import paho.mqtt.client as mqtt
import json
import os
import time
import tempfile
import threading

REALTIME_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'realtime_pdn_data.json')
save_lock = threading.Lock()

def save_to_json(latest_sensors):
    """Save latest sensor readings to JSON atomically (no corruption)."""
    try:
        with save_lock:
            import tempfile, os, json
            temp_fd, temp_path = tempfile.mkstemp()
            with os.fdopen(temp_fd, 'w') as tmp_file:
                json.dump([
                    {
                        "sensor_id": sid,
                        "subdivision": entry.get("subdivision"),
                        "value": entry.get("value"),
                        "lat": entry.get("lat"),
                        "lon": entry.get("lon")
                    }
                    for sid, entry in latest_sensors.items()
                ], tmp_file, indent=2)
            os.replace(temp_path, REALTIME_JSON)
    except Exception as e:
        print(f"❌ Error saving realtime data: {e}")

def start_mqtt(LATEST_SENSORS, alert_callback):
    broker = "test.mosquitto.org"
    port = 1883
    topic = "rainfall/+/data"

    print(f"🌐 Connecting to MQTT broker {broker}:{port}, topic={topic}", flush=True)

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("✅ MQTT connected successfully")
            client.subscribe(topic)
        else:
            print(f"❌ MQTT connection failed: {rc}")

    def on_disconnect(client, userdata, rc):
        print(f"⚠️ MQTT disconnected (rc={rc}), retrying...")

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            sensor_id = msg.topic.split("/")[1]

            entry = {
                "ts": int(time.time()),
                "subdivision": payload.get("subdivision"),
                "value": float(payload.get("value", 0)),
                "lat": float(payload.get("lat")),
                "lon": float(payload.get("lon"))
            }

            LATEST_SENSORS[sensor_id] = entry
            save_to_json(LATEST_SENSORS)
            alert_callback(sensor_id, entry)

            print(f"📡 MQTT update -> {sensor_id}: {entry}")

        except Exception as e:
            print(f"❌ Error processing MQTT message: {e}")

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    try:
        client.connect(broker, port, 60)
        print("🚀 Starting MQTT loop...")
        client.loop_forever()
    except Exception as e:
        print(f"❌ MQTT connection error: {e}")
