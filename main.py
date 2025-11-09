import os
import time
from datetime import datetime
import requests
from googleapiclient.discovery import build

# ==============================
# ⚙️ Configuration (Environment)
# ==============================
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")
VIDEO_ID = os.getenv("VIDEO_ID")  # optional
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TARGET_USERNAME = os.getenv("TARGET_USERNAME", "Sunshine 🌞")

# ==============================
# 🕐 Night time check (9 PM–3 AM)
# ==============================
def is_night_time():
    now = datetime.now().hour
    return now >= 21 or now < 3

# ==============================
# 🎥 Get live video ID (if not set)
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
    else:
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
    else:
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

    while True:
        if not is_night_time():
            print("🌞 Daytime — sleeping 5 min")
            time.sleep(300)
            continue

        video_id = VIDEO_ID or get_live_video_id()
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

                for item in res["items"]:
                    author = item["authorDetails"]["displayName"]
                    if TARGET_USERNAME.lower() in author.lower():
                        send_telegram(f"🌞 {author} just sent a message in live chat!")

                next_page = res.get("nextPageToken")
                time.sleep(10)
            except Exception as e:
                print("⚠️ Error:", e)
                time.sleep(30)

# ==============================
# ▶️ Run
# ==============================
if __name__ == "__main__":
    main()
