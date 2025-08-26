# IoT Rainfall Prediction — Enhanced

## Overview
This project includes:
- Flask backend with REST prediction endpoint
- MQTT ingestion (paho-mqtt) and a REST `/sensor` endpoint
- Simple alerting hooks (FCM / Twilio placeholders)
- Model wrapper that can combine LSTM predictions with realtime sensor data
- Minimal Flutter app skeleton that subscribes to MQTT alerts and can request predictions

## Environment variables to set
- MQTT_BROKER (default: test.mosquitto.org)
- MQTT_PORT (default: 1883)
- MQTT_TOPIC (default: rainfall/sensors/#)
- OWM_API_KEY (OpenWeatherMap API key, optional)
- FCM_SERVER_KEY (optional for push)
- TWILIO_SID / TWILIO_TOKEN / TWILIO_FROM / TWILIO_TO (optional for SMS)
- ALERT_THRESHOLD_MM (default: 50)

## Run backend locally
1. Create virtualenv and install:
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

2. Run:
   python backend/app.py

## MQTT message example
Topic: rainfall/sensors/<sensor_id>
Payload:
{"sensor_id":"sensor1","value":60.5,"lat":12.3,"lon":78.9}

## Notes and next steps
- Persist sensor data to a DB for history and charts
- Register device tokens for FCM and implement secure push notifications
- Harden the API (auth, rate limits, TLS)
- Add Docker Compose for local dev
