# backend/app.py
import os
import sys
import threading
import time
import json
import pandas as pd
import plotly.express as px
import folium
from flask import Flask, request, jsonify, render_template

# ---------------- CONFIG PATHS ---------------- #
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))
DATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'Rain_data.csv')
MODEL_DIR = os.path.join(PROJECT_ROOT, 'backend', 'model')
MAP_JSON = os.path.join(PROJECT_ROOT, 'data', 'map_generated_data.json')
REALTIME_JSON = os.path.join(PROJECT_ROOT, 'data', 'realtime_pdn_data.json')
STATIC_DIR = os.path.join(PROJECT_ROOT, 'static')

os.makedirs(STATIC_DIR, exist_ok=True)
sys.path.append(MODEL_DIR)

try:
    from model.predict_rainfall import predict_next_rainfall, predict_using_realtime
except Exception:
    from backend.model.predict_rainfall import predict_next_rainfall, predict_using_realtime

from mqtt_client import start_mqtt
from alerts import check_and_send_alert

# --- ADD: CORS for API calls --- #
try:
    from flask_cors import CORS
except ImportError:
    CORS = None

# ---------------- FLASK APP ---------------- #
app = Flask(__name__, template_folder=os.path.join(PROJECT_ROOT, 'templates'), static_folder=STATIC_DIR)
if CORS:
    CORS(app)

LATEST_SENSORS = {}

"""
# ---------------- FCM TOKEN STORAGE ---------------- #
FCM_TOKENS_FILE = os.path.join(PROJECT_ROOT, 'data', 'fcm_tokens.json')

def _load_tokens():
    try:
        with open(FCM_TOKENS_FILE, 'r') as f:
            return set(json.load(f))
    except Exception:
        return set()

def _save_tokens(tokens):
    os.makedirs(os.path.dirname(FCM_TOKENS_FILE), exist_ok=True)
    with open(FCM_TOKENS_FILE, 'w') as f:
        json.dump(list(tokens), f, indent=2)

FCM_TOKENS = _load_tokens()
"""

# ---------------- HOME ---------------- #
@app.route('/', methods=['GET', 'POST'])
def home():
    prediction = None
    if request.method == 'POST':
        subdivision = request.form.get('subdivision', '').strip()
        try:
            prediction_val = predict_next_rainfall(subdivision)
            prediction = f"{subdivision.title()}: {prediction_val} mm"
        except Exception as e:
            prediction = f"Error: {str(e)}"
    return render_template('index.html', prediction=prediction)

# ---------------- PREDICT API ---------------- #
@app.route('/predict', methods=['POST'])
def api_predict():
    data = request.get_json() or {}
    subdivision = data.get('subdivision', '')
    use_realtime = data.get('use_realtime', False)
    sensor_id = data.get('sensor_id')

    try:
        if use_realtime and sensor_id and sensor_id in LATEST_SENSORS:
            sensor = LATEST_SENSORS[sensor_id]
            prediction = predict_using_realtime(subdivision, sensor)
        else:
            prediction = predict_next_rainfall(subdivision)

        return jsonify({
            'subdivision': subdivision.title(),
            'predicted_rainfall': prediction
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ---------------- SENSOR POST ---------------- #
@app.route('/sensor', methods=['POST'])
def sensor_post():
    data = request.get_json() or {}
    sensor_id = data.get('sensor_id')
    value = data.get('value')
    if not sensor_id or value is None:
        return jsonify({'error': 'sensor_id and value required'}), 400

    entry = {
        'ts': data.get('ts', int(time.time())),
        'value': float(value),
        'lat': data.get('lat'),
        'lon': data.get('lon'),
        'subdivision': data.get('subdivision')
    }
    LATEST_SENSORS[sensor_id] = entry

    # Existing Twilio + log alerts
    threading.Thread(target=check_and_send_alert, args=(sensor_id, entry), daemon=True).start()

    # NEW: Send PWA push alerts
    threading.Thread(target=lambda: try_pwa_push(sensor_id, entry), daemon=True).start()

    return jsonify({'status': 'ok'})

@app.route('/sensors/latest')
def sensors_latest():
    return jsonify(LATEST_SENSORS)

# ---------------- MAP GENERATION ---------------- #
def generate_map_data():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError("Rain_data.csv not found.")

    df = pd.read_csv(DATA_PATH)
    df.columns = [str(col).strip().lower() for col in df.columns]

    if not {'subdivision', 'latitude', 'longitude'}.issubset(df.columns):
        raise ValueError("CSV must contain 'subdivision', 'latitude', 'longitude' columns.")

    results = []
    for _, row in df.iterrows():
        if pd.isna(row['latitude']) or pd.isna(row['longitude']):
            continue
        try:
            pred = predict_next_rainfall(row['subdivision'])
        except Exception:
            pred = None

        results.append({
            "subdivision": row['subdivision'],
            "latitude": float(row['latitude']),
            "longitude": float(row['longitude']),
            "predicted_rainfall": float(pred) if pred is not None else None
        })

    with open(MAP_JSON, 'w') as f:
        json.dump(results, f, indent=2)
    return results

@app.route('/generate-map-data')
def generate_map_data_route():
    try:
        data = generate_map_data()
        return jsonify({"status": "ok", "count": len(data), "file": MAP_JSON})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ---------------- FOLIUM MAP (PREDICTED) ---------------- #
@app.route('/folium-map')
def folium_map_pred():
    if not os.path.exists(MAP_JSON):
        return jsonify({"error": "Run /generate-map-data first"}), 404
    with open(MAP_JSON) as f:
        data = json.load(f)
    df = pd.DataFrame(data)

    m = folium.Map(location=[22.9734, 78.6569], zoom_start=5, tiles="CartoDB positron")

    colors = [
        "red", "blue", "green", "orange", "purple", "darkred", "lightred",
        "beige", "darkblue", "darkgreen", "cadetblue", "darkpurple", "pink",
        "lightblue", "lightgreen", "gray", "black", "lightgray"
    ]

    for idx, row in df.iterrows():
        color_choice = colors[idx % len(colors)]
        val = row.get('predicted_rainfall', 0) or 0

        popup_html = f"""
        <div style='font-size:14px; font-family:Arial;'>
            <b style='font-size:15px; color:black;'>{row['subdivision']}</b><br>
            <b style='font-size:14px; color:blue;'>{val} mm (Predicted)</b>
        </div>
        """

        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=max(6, min(val / 10, 15)),
            popup=folium.Popup(popup_html, max_width=250),
            color=color_choice,
            fill=True,
            fill_color=color_choice,
            fill_opacity=0.85
        ).add_to(m)

    file_path = os.path.join(STATIC_DIR, 'folium_pred.html')
    m.save(file_path)
    return app.send_static_file('folium_pred.html')

# ---------------- FOLIUM MAP (REALTIME) ---------------- #
@app.route('/folium-realtime')
def folium_map_realtime():
    if not os.path.exists(REALTIME_JSON):
        return jsonify({"error": "realtime_pdn_data.json not found. Please run mqtt_publisher.py first."}), 404

    try:
        with open(REALTIME_JSON) as f:
            data = json.load(f)
    except Exception as e:
        return jsonify({"error": f"Error reading JSON: {str(e)}"}), 500

    if not data:
        return jsonify({"error": "No real-time sensor data in file"}), 404

    df = pd.DataFrame(data)
    df = df.sort_values("sensor_id").drop_duplicates(subset=["subdivision"], keep="last")

    m = folium.Map(location=[22.9734, 78.6569], zoom_start=5, tiles="CartoDB positron")

    colors = [
        "red", "blue", "green", "orange", "purple", "darkred", "lightred",
        "beige", "darkblue", "darkgreen", "cadetblue", "darkpurple", "pink",
        "lightblue", "lightgreen", "gray", "black", "lightgray"
    ]

    for idx, row in df.iterrows():
        color_choice = colors[idx % len(colors)]
        rainfall_val = float(row.get('value', 0))

        if rainfall_val > 150:
            alert_icon, alert_color = "⛈ Severe Rain", "darkred"
        elif rainfall_val > 100:
            alert_icon, alert_color = "🌧 Heavy Rain", "orange"
        else:
            alert_icon, alert_color = "☁ Normal", "green"

        popup_html = f"""
        <div style='font-size:14px; font-family:Arial;'>
            <b style='font-size:15px; color:black;'>{row.get('sensor_id', idx+1)} - {row.get('subdivision', 'N/A')}</b><br>
            <b style='font-size:14px; color:{alert_color};'>{rainfall_val} mm</b><br>
            <span style='font-size:13px; color:{alert_color};'>{alert_icon}</span>
        </div>
        """

        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=max(6, min(rainfall_val / 10, 15)),
            popup=folium.Popup(popup_html, max_width=250),
            color=color_choice,
            fill=True,
            fill_color=color_choice,
            fill_opacity=0.85
        ).add_to(m)

    file_path = os.path.join(STATIC_DIR, 'folium_realtime.html')
    m.save(file_path)
    return app.send_static_file('folium_realtime.html')

# ---------------- PLOTLY MAP ---------------- #
@app.route('/plotly-map')
def plotly_map():
    if not os.path.exists(MAP_JSON):
        return jsonify({"error": "Run /generate-map-data first"}), 404
    with open(MAP_JSON) as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    if df.empty:
        return jsonify({"error": "No data available"}), 400

    fig = px.scatter_mapbox(
        df, lat='latitude', lon='longitude',
        color='predicted_rainfall', size='predicted_rainfall',
        hover_name='subdivision',
        hover_data={'latitude': True, 'longitude': True, 'predicted_rainfall': True},
        zoom=4, height=750, color_continuous_scale=px.colors.sequential.Viridis
    )
    fig.update_layout(mapbox_style='open-street-map', margin={'r':0,'t':0,'l':0,'b':0})

    file_path = os.path.join(STATIC_DIR, 'plotly_map.html')
    fig.write_html(file_path, full_html=False, include_plotlyjs='cdn')
    return app.send_static_file('plotly_map.html')

# ---------------- PWA PUSH ALERT SUPPORT ---------------- #
from pywebpush import webpush, WebPushException

VAPID_PUBLIC_KEY = "YOUR_PUBLIC_KEY"   # Replace with generated
VAPID_PRIVATE_KEY = "YOUR_PRIVATE_KEY" # Replace with generated
VAPID_CLAIMS = {"sub": "mailto:you@example.com"}

SUBSCRIPTIONS_FILE = os.path.join(PROJECT_ROOT, 'data', 'subscriptions.json')

def _load_subscriptions():
    try:
        with open(SUBSCRIPTIONS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def _save_subscriptions(subs):
    os.makedirs(os.path.dirname(SUBSCRIPTIONS_FILE), exist_ok=True)
    with open(SUBSCRIPTIONS_FILE, 'w') as f:
        json.dump(subs, f, indent=2)

SUBSCRIPTIONS = _load_subscriptions()

@app.route("/subscribe", methods=["POST"])
def subscribe():
    sub = request.get_json()
    SUBSCRIPTIONS.append(sub)
    _save_subscriptions(SUBSCRIPTIONS)
    return jsonify({"message": "Subscribed successfully!"})

def send_push_to_all(title, body):
    for sub in SUBSCRIPTIONS:
        try:
            webpush(
                subscription_info=sub,
                data=json.dumps({"title": title, "message": body}),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS
            )
        except WebPushException as e:
            print("Push failed:", e)

def try_pwa_push(sensor_id, entry):
    try:
        value = float(entry.get('value', 0))
        if value >= 100:  # Example threshold
            title = '⚠ Heavy Rain Alert'
            body = f"Sensor {sensor_id} reported {value} mm."
            send_push_to_all(title, body)
    except Exception as e:
        print("PWA push error:", e)

@app.route("/alerts/test-pwa", methods=["POST"])
def test_pwa_alert():
    data = request.get_json() or {}
    send_push_to_all(data.get("title", "🌧 Rain Alert"), data.get("body", "Test push from backend"))
    return jsonify({"status": "sent"})

# ---------------- MAIN ---------------- #
if __name__ == '__main__':
    threading.Thread(target=start_mqtt, args=(LATEST_SENSORS, check_and_send_alert), daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)