# backend/run_alerts.py

print("🚀 run_alerts.py starting...")  # DEBUG

from mqtt_client import start_mqtt
from alerts import check_and_send_alert

def alert_handler(sensor_id, entry):
    """Wrapper around check_and_send_alert for debug logging."""
    print(f"🚨 ALERT TRIGGERED -> Checking sensor {sensor_id} ({entry.get('subdivision')}) value={entry.get('value')}")
    check_and_send_alert(sensor_id, entry)

if __name__ == "__main__":
    print("🚀 Entering __main__ block")  # DEBUG
    LATEST_SENSORS = {}
    start_mqtt(LATEST_SENSORS, alert_handler)
