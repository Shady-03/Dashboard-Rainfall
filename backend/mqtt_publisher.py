# backend/mqtt_publisher.py
import paho.mqtt.client as mqtt
import pandas as pd
import json
import time
import random

CSV_PATH = "data/Rain_data.csv"
BROKER = "test.mosquitto.org"
PORT = 1883

# Load CSV
df = pd.read_csv(CSV_PATH)

# Normalize column names
df.columns = [str(col).strip().lower() for col in df.columns]

# Keep only required columns
required_cols = {"subdivision", "latitude", "longitude"}
if not required_cols.issubset(df.columns):
    raise ValueError(f"CSV must contain columns: {required_cols}")

# ✅ Deduplicate subdivisions (keep first row for each)
df_unique = df.drop_duplicates(subset=["subdivision"], keep="first").reset_index(drop=True)

print(f"✅ Using {len(df_unique)} unique subdivisions as sensors")

# MQTT client
client = mqtt.Client()
client.connect(BROKER, PORT, 60)

while True:
    for idx, row in df_unique.iterrows():
        sensor_id = f"sensor{idx+1}"  # 1 sensor per subdivision
        value = round(random.uniform(50, 150), 2)  # Random rain value for demo

        payload = {
            "subdivision": row["subdivision"],
            "value": value,
            "lat": float(row["latitude"]),
            "lon": float(row["longitude"])
        }

        topic = f"rainfall/{sensor_id}/data"
        client.publish(topic, json.dumps(payload))
        print(f"📤 Sent -> {topic}: {payload}")
        time.sleep(1)  # Wait 1s between sensors

    print("🔄 All subdivisions updated, restarting cycle...\n")
    time.sleep(5)  # Wait before next full cycle
