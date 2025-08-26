# send_all_sensors.py
import pandas as pd
import requests
import time
import json
import os

# Paths
csv_path = "data/Rain_data.csv"
realtime_json_path = "data/realtime_pdn_data.json"

# Flask server base URL
BASE_URL = "http://127.0.0.1:5000"

# Load dataset and normalize column names
df = pd.read_csv(csv_path)
df.columns = df.columns.str.lower().str.strip()

# Ensure required columns exist
required_cols = ["subdivision", "latitude", "longitude"]
for col in required_cols:
    if col not in df.columns:
        raise ValueError(f"Missing required column: {col}")

# Get unique subdivisions with their first lat/lon
unique_subdivisions = df.groupby("subdivision").first().reset_index()

# Store all sensor data in a list for saving
all_sensor_data = []

# Send sensor data for each subdivision
for idx, row in unique_subdivisions.iterrows():
    sensor_data = {
        "sensor_id": f"sensor{idx+1}",
        "value": round(float(row.get("value", 75)), 2),  # default rainfall value if missing
        "lat": float(row["latitude"]),
        "lon": float(row["longitude"]),
        "subdivision": row["subdivision"]
    }
    all_sensor_data.append(sensor_data)

    resp = requests.post(f"{BASE_URL}/sensor", json=sensor_data)
    print(f"Sent: {sensor_data} -> Status {resp.status_code}")
    time.sleep(0.2)  # small delay to avoid flooding

# Save all sensor data to JSON file
os.makedirs(os.path.dirname(realtime_json_path), exist_ok=True)
with open(realtime_json_path, "w") as f:
    json.dump(all_sensor_data, f, indent=2)
print(f"\n✅ Real-time sensor data saved to {realtime_json_path}")

# Automatically trigger generate-map-data
print("\nTriggering /generate-map-data...")
map_resp = requests.get(f"{BASE_URL}/generate-map-data")
if map_resp.status_code == 200:
    print("Map data generated successfully!")
else:
    print(f"Failed to generate map data: {map_resp.text}")
