import os
import time
from datetime import datetime, timedelta, timezone
import requests
from googleapiclient.discovery import build

# ==============================
# ⚙️ Configuration (Environment)
# ==============================
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")
CHAT_ID = os.getenv("CHAT_ID")  # optional: predefined live video ID
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TARGET_USERNAME = os.getenv("TARGET_USERNAME", "Pallavi Singh")

IST = timezone(timedelta(hours=5, minutes=30))
ALERT_GAP = 10  # seconds between alerts for the same user

# ==============================
# 🕐 Night time check (9 PM–5 AM)
# ==============================
def is_night_time():
    now_hour = datetime.now(IST).hour
    return now_hour >= 21 or now_hour < 12

# ==============================
# 🎥 Get live video ID from channel
# ==============================
def get_live_video_id():
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
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
# 💬 Get live chat ID
# ==============================
def get_live_chat_id(video_id):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
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
    requests.post(url, json=payload)

# ==============================
# 🧠 Main Loop
# ==============================
def main():
    print("🚀 YouTube Chat Monitor Started")
    last_alert_time = {}  # track last alert per user

    while True:
        if not is_night_time():
            print("🌞 Daytime — sleeping 5 min")
            time.sleep(300)
            continue

        video_id = CHAT_ID #or #get_live_video_id()
        if not video_id:
            print("❌ No live video found")
            time.sleep(60)
            continue

        live_chat_id = get_live_chat_id(video_id)
        if not live_chat_id:
            print("❌ No live chat found")
            time.sleep(60)
            continue

        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        next_page = None

        while is_night_time():
            try:
                res = youtube.liveChatMessages().list(
                    liveChatId=live_chat_id,
                    part="snippet,authorDetails",
                    pageToken=next_page
                ).execute()

                polling_interval = res.get("pollingIntervalMillis", 5000) / 1000  # seconds

                for item in res.get("items", []):
                    author = item["authorDetails"]["displayName"]
                    message = item["snippet"]["displayMessage"]
                    now = time.time()

                    if TARGET_USERNAME.lower() in author.lower():
                        last_time = last_alert_time.get(author, 0)
                        if now - last_time >= ALERT_GAP:
                            alert_text = f"🌞 {author} sent a message: {message}"
                            send_telegram(alert_text)
                            print(alert_text)
                            last_alert_time[author] = now

                next_page = res.get("nextPageToken")
                time.sleep(polling_interval)
            except Exception as e:
                print("⚠️ Error:", e)
                time.sleep(30)

# ==============================
# ▶️ Run
# ==============================
if __name__ == "__main__":
    main()
