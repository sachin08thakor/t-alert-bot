import os
import time
from datetime import datetime, timedelta, timezone
import requests
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ==============================
# ⚙️ Configuration (Environment)
# ==============================
API_KEYS = [
    os.getenv("YOUTUBE_API_KEY_1"),
    os.getenv("YOUTUBE_API_KEY_2")
]
current_key_index = 0

CHANNEL_ID = os.getenv("CHANNEL_ID")
CHAT_ID = os.getenv("CHAT_ID")  # optional: predefined live video ID
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TARGET_USERNAME = os.getenv("TARGET_USERNAME", "Sunshine 🌞")

# India Standard Time (UTC +5:30)
IST = timezone(timedelta(hours=5, minutes=30))
ALERT_GAP = 10  # seconds between same user alerts

# ==============================
# 🧠 API Key Handling
# ==============================
def get_youtube():
    """Return YouTube service with current API key"""
    key = API_KEYS[current_key_index]
    return build("youtube", "v3", developerKey=key)

def switch_api_key():
    """Switch to next API key if quota exceeded"""
    global current_key_index
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    print(f"🔁 Switched to YouTube API key #{current_key_index + 1}")

# ==============================
# 🕐 Active Time (11 PM – 2 AM)
# ==============================
def is_active_time():
    now_hour = datetime.now(IST).hour
    return now_hour >= 21 or now_hour <= 13  # 23:00–01:59 IST

# ==============================
# 🎥 Get Live Video ID
# ==============================
def get_live_video_id(youtube):
    req = youtube.search().list(
        part="id",
        channelId=CHANNEL_ID,
        eventType="live",
        type="video"
    )
    res = req.execute()
    items = res.get("items", [])
    if items:
        return items[0]["id"]["videoId"]
    return None

# ==============================
# 💬 Get Live Chat ID
# ==============================
def get_live_chat_id(youtube, video_id):
    req = youtube.videos().list(part="liveStreamingDetails", id=video_id)
    res = req.execute()
    items = res.get("items", [])
    if items:
        return items[0]["liveStreamingDetails"].get("activeLiveChatId")
    return None

# ==============================
# 📩 Send Telegram Message
# ==============================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("⚠️ Telegram send error:", e)

# ==============================
# 🧠 Main Logic
# ==============================
def main():
    print("🚀 YouTube Chat Monitor Started (Dual API Mode)")
    last_alert_time = {}
    youtube = get_youtube()

    while True:
        # Run only in active hours (11 PM–2 AM IST)
        if not is_active_time():
            print("🌞 Outside 11 PM–3 AM — sleeping 5 minutes")
            time.sleep(300)
            continue

        # Use predefined video/chat or detect automatically
        video_id = CHAT_ID  # or get_live_video_id(youtube)
        if not video_id:
            print("❌ No live video found")
            time.sleep(60)
            continue

        live_chat_id = get_live_chat_id(youtube, video_id)
        if not live_chat_id:
            print("❌ No live chat found")
            time.sleep(60)
            continue

        next_page = None

        while is_active_time():
            try:
                res = youtube.liveChatMessages().list(
                    liveChatId=live_chat_id,
                    part="snippet,authorDetails",
                    pageToken=next_page
                ).execute()

                polling_interval = max(8, res.get("pollingIntervalMillis", 5000) / 1000)

                for item in res.get("items", []):
                    author = item["authorDetails"]["displayName"]
                    message = item["snippet"]["displayMessage"]
                    now = time.time()

                    if TARGET_USERNAME.lower() in author.lower():
                        last_time = last_alert_time.get(author, 0)
                        if now - last_time >= ALERT_GAP:
                            alert_text = f"🌞 {author} sent: {message}"
                            send_telegram(alert_text)
                            print(alert_text)
                            last_alert_time[author] = now

                next_page = res.get("nextPageToken")
                time.sleep(polling_interval)

            except HttpError as e:
                if e.resp.status == 403:
                    print("⚠️ Quota exceeded or access forbidden. Switching API key...")
                    switch_api_key()
                    youtube = get_youtube()
                    time.sleep(30)
                else:
                    print("⚠️ API error:", e)
                    time.sleep(30)
            except Exception as e:
                print("⚠️ Unexpected error:", e)
                time.sleep(30)

# ==============================
# ▶️ Run
# ==============================
if __name__ == "__main__":
    main()
