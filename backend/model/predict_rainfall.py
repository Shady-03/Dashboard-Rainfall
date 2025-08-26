# backend/model/predict_rainfall.py
import os
os.environ.setdefault('TF_ENABLE_ONEDNN_OPTS', '0')

import numpy as np
import pandas as pd
import joblib
import difflib
from keras.models import load_model
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..', '..'))
DATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'Rain_data.csv')

OWM_KEY = os.environ.get('OWM_API_KEY')

def fetch_current_weather(lat, lon):
    if not OWM_KEY or lat is None or lon is None:
        return None
    try:
        url = f'https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely,hourly&appid={OWM_KEY}&units=metric'
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print('OWM fetch error', e)
        return None

def predict_next_rainfall(subdivision: str):
    subdivision = subdivision.strip().upper()
    model_name = subdivision.replace(' ', '_')

    model_path = os.path.join(BASE_DIR, f"{model_name}_lstm.keras")
    scaler_path = os.path.join(BASE_DIR, f"{model_name}_scaler.pkl")

    if not os.path.exists(model_path) or not os.path.exists(scaler_path):
        raise FileNotFoundError(f"Model or scaler not found for subdivision: {subdivision}")

    model = load_model(model_path)
    scaler = joblib.load(scaler_path)

    df = pd.read_csv(DATA_PATH)
    df['SUBDIVISION'] = df['SUBDIVISION'].str.strip().str.upper()

    all_subdivisions = df['SUBDIVISION'].unique()
    closest = difflib.get_close_matches(subdivision, all_subdivisions, n=1, cutoff=0.6)
    if not closest:
        raise ValueError(f"Subdivision '{subdivision}' not found")

    matched = closest[0]
    data = df[df['SUBDIVISION'] == matched].sort_values('YEAR')
    last_5_values = data['ANNUAL'].values[-5:]

    if len(last_5_values) < 5:
        raise ValueError('Not enough data for prediction')

    scaled_input = scaler.transform(np.array(last_5_values).reshape(-1, 1))
    X_input = scaled_input.reshape(1, 5, 1)
    pred_scaled = model.predict(X_input)
    prediction = float(scaler.inverse_transform(pred_scaled)[0][0])

    return round(prediction, 2)

def predict_using_realtime(subdivision: str, sensor_entry: dict):
    base_pred = predict_next_rainfall(subdivision)
    try:
        sensor_val = float(sensor_entry.get('value', 0))
        adjusted = 0.6 * base_pred + 0.4 * sensor_val
        lat, lon = sensor_entry.get('lat'), sensor_entry.get('lon')
        w = fetch_current_weather(lat, lon)
        if w and 'current' in w and w['current'].get('rain'):
            adjusted *= 1.1
        return round(float(adjusted), 2)
    except Exception as e:
        print('Realtime adjust failed', e)
        return round(float(base_pred), 2)
