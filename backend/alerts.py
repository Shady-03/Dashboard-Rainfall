# backend/alerts.py
import os
import time
import json
import requests
from dotenv import load_dotenv

# For WebPush
from pywebpush import webpush, WebPushException

# ---------------- LOAD CONFIG ---------------- #
load_dotenv()

THRESHOLD_MM = float(os.getenv("ALERT_THRESHOLD_MM", "50"))
COOLDOWN_SEC = int(os.getenv("ALERT_COOLDOWN_SEC", "600"))

# Telegram config
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# WebPush config
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY")
VAPID_CLAIMS = {"sub": "mailto:your-email@example.com"}  # update this
SUBSCRIPTIONS_FILE = os.path.join(os.path.dirname(__file__), "data", "pwa_subscriptions.json")

# Prevent spamming alerts
LAST_ALERTS = {}  # {sensor_id: last_sent_timestamp}

# ---------------- TELEGRAM ---------------- #
def send_telegram_message(text: str, silent: bool = False) -> bool:
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_notification": silent,
    }

    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            print(f"✅ Telegram alert sent -> {text[:50]}...")
            return True
        else:
            print(f"❌ Telegram send failed [{r.status_code}]: {r.text}")
            return False
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False

# ---------------- WEB PUSH ---------------- #
def send_webpush_notification(payload: dict) -> bool:
    if not VAPID_PRIVATE_KEY:
        print("❌ Missing VAPID_PRIVATE_KEY")
        return False

    try:
        if not os.path.exists(SUBSCRIPTIONS_FILE):
            print("⚠️ No PWA subscriptions found")
            return False

        with open(SUBSCRIPTIONS_FILE, "r") as f:
            subs = json.load(f)

        for sub in subs:
            try:
                webpush(
                    subscription_info=sub,
                    data=json.dumps(payload),
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims=VAPID_CLAIMS,
                )
                print("✅ WebPush sent to browser")
            except WebPushException as e:
                print(f"❌ WebPush error: {e}")
        return True
    except Exception as e:
        print(f"❌ WebPush general error: {e}")
        return False

# ---------------- ALERT CHECK ---------------- #
def check_and_send_alert(sensor_id: str, entry: dict):
    """
    Called from mqtt_client when new sensor data arrives.
    entry = {
      "ts": 172...,
      "subdivision": "...",
      "value": 123.4,
      "lat": 12.34,
      "lon": 56.78
    }
    """
    try:
        value = float(entry.get("value", 0))
        subdivision = entry.get("subdivision") or "Unknown"
        lat = entry.get("lat")
        lon = entry.get("lon")
        now = time.time()

        # Cooldown check
        last_sent = LAST_ALERTS.get(sensor_id, 0)
        if now - last_sent < COOLDOWN_SEC:
            return

        # Determine alert level
        if value > 150:
            title = "⛈ *Severe Rain Alert*"
        elif value > 100:
            title = "🌧 *Heavy Rain Alert*"
        elif value > THRESHOLD_MM:
            title = "☔ *Moderate Rain Alert*"
        else:
            return  # No alert

        # Build message
        lines = [
            title,
            f"• Sensor: `{sensor_id}`",
            f"• Subdivision: {subdivision}",
            f"• Amount: *{value:.1f} mm*",
            f"• Threshold: {THRESHOLD_MM} mm",
        ]
        if lat is not None and lon is not None:
            lines.append(f"• Map: https://maps.google.com/?q={lat},{lon}")

        message = "\n".join(lines)

        # ✅ Send Telegram
        sent_telegram = send_telegram_message(message)

        # ✅ Send PWA/WebPush
        payload = {"title": title, "body": f"{subdivision}: {value:.1f} mm rain"}
        sent_webpush = send_webpush_notification(payload)

        # Update cooldown only if at least one channel succeeded
        if sent_telegram or sent_webpush:
            LAST_ALERTS[sensor_id] = now

    except Exception as e:
        print(f"❌ Alert check error: {e}")
