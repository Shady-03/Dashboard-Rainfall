import requests

BOT_TOKEN = "7578380854:AAHFJ9UcXjRs_ukqQVrlOWDhjJi_PIofi6E"
CHAT_ID = "5047575122"   # <--- your chat ID

def send_message(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        r = requests.post(url, json=payload, timeout=10)
        print("Status:", r.status_code)   # DEBUG
        print("Response:", r.text)        # DEBUG
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    send_message("✅ Test: Rainfall Alert system connected!")
