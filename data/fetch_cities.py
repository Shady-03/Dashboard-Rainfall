import os
import json
import requests

print("🚀 Step 1: Starting fetch_cities.py")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
CITIES_FILE = os.path.join(DATA_DIR, "cities.json")

print(f"📂 Step 2: Data folder is {DATA_DIR}")
print(f"📄 Step 3: Output file will be {CITIES_FILE}")

# API details
API_KEY = "sk-live-ACDpTfBq4PGg0K1cEeQ6VSjf8wpBM3lPOuoxs7am"  # <-- your key
BASE_URL = "https://weather.indianapi.in"
headers = {"x-api-key": API_KEY}

def fetch_cities():
    print("🌍 Step 4: Preparing to call Indian API for city list...")
    try:
        url = f"{BASE_URL}/india/cities"
        print(f"➡️ Step 5: Calling {url}")
        resp = requests.get(url, headers=headers, timeout=20)
        print(f"✅ Step 6: Got response with status {resp.status_code}")
        resp.raise_for_status()
        data = resp.json()
        print(f"📊 Step 7: Received {len(data)} records from API")
    except Exception as e:
        print("❌ ERROR in API call:", e)
        return []

    # Normalize into list of dicts
    cities = []
    for i, city in enumerate(data, start=1):
        cid = city.get("id")
        name = city.get("name")
        state = city.get("state")
        lat, lon = city.get("lat"), city.get("lon")

        if cid and lat and lon:
            cities.append({
                "id": str(cid),
                "name": name,
                "state": state,
                "lat": float(lat),
                "lon": float(lon)
            })

        if i % 50 == 0:
            print(f"   ...processed {i} cities so far")

    print(f"🏁 Step 8: Processed total {len(cities)} valid cities")
    return cities

def save_cities(cities):
    print("💾 Step 9: Saving cities to file...")
    with open(CITIES_FILE, "w", encoding="utf-8") as f:
        json.dump(cities, f, indent=2, ensure_ascii=False)
    print(f"✅ Step 10: Saved {len(cities)} cities to {CITIES_FILE}")

if __name__ == "__main__":
    print("🔄 Step 11: Running main()")
    cities = fetch_cities()
    if cities:
        save_cities(cities)
    else:
        print("⚠️ Step 12: No cities fetched. Please check API key or endpoint.")
