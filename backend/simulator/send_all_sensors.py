# simulator/send_all_sensors.py
import paho.mqtt.client as mqtt
import pandas as pd
import json
import random
import time
import os

# MQTT broker config
BROKER = "localhost"  # change if your broker is remote
PORT = 1883
TOPIC_TEMPLATE = "rainfall/sensor{}/data"

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "Rain_data.csv")

# Load dataset
df = pd.read_csv(DATA_PATH)
df.columns = [col.strip().lower() for col in df.columns]

# Required columns
if not {"subdivision", "latitude", "longitude"}.issubset(df.columns):
    raise ValueError("CSV must contain subdivision, latitude, longitude columns.")

# MQTT client setup
client = mqtt.Client()
client.connect(BROKER, PORT, 60)

def send_sensor_data():
    for i, row in df.iterrows():
        sensor_id = i + 1
        payload = {
            "sensor_id": f"sensor{sensor_id}",
            "subdivision": row["subdivision"],
            "lat": float(row["latitude"]),
            "lon": float(row["longitude"]),
            "value": round(random.uniform(10, 150), 1)  # random rainfall in mm
        }
        topic = TOPIC_TEMPLATE.format(sensor_id)
        client.publish(topic, json.dumps(payload))
        print(f"Published to {topic}: {payload}")

print("Starting simulated sensor updates...")
try:
    while True:
        send_sensor_data()
        time.sleep(10)  # send updates every 10 seconds
except KeyboardInterrupt:
    print("Simulation stopped.")
