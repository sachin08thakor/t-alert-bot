import os
import time
from datetime import datetime
from googleapiclient.discovery import build
import requests

# CONFIG
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TARGET_USERNAME = os.getenv("TARGET_USERNAME", "Sunshine 🌞")

def is_night_time():
    hour = datetime.now().hour
    return hour >= 21 or hour < 3

def get_live_chat_id():
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    search = youtube.search().list(
        part="id", channelId=CHANNEL_ID, eventType="live", type="video"
    ).execute()
    items = search.get("items", [])
    if not items:
        print("⚠️ No live stream found.")
        return None
    video_id = items[0]["id"]["videoId"]
    video = youtube.videos().list(part="liveStreamingDetails", id=video_id).execute()
    return video["items"][0]["liveStreamingDetails"].get("activeLiveChatId")

def get_live_messages(live_chat_id, page_token=None):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    req = youtube.liveChatMessages().list(
        liveChatId=live_chat_id, part="snippet,authorDetails", pageToken=page_token
    )
    return req.execute()

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    r = requests.post(url, data=data)
    if not r.ok:
        print("⚠️ Telegram error:", r.text)

def monitor():
    print("🚀 Starting YouTube → Telegram Night Monitor")
    live_chat_id = get_live_chat_id()
    if not live_chat_id:
        print("❌ No active chat ID found.")
        return
    next_page_token = None
    while True:
        try:
            if not is_night_time():
                print("☀️ Sleeping until night hours (9 PM – 3 AM)")
                time.sleep(300)
                continue
            resp = get_live_messages(live_chat_id, next_page_token)
            next_page_token = resp.get("nextPageToken")
            for msg in resp.get("items", []):
                author = msg["authorDetails"]["displayName"]
                text = msg["snippet"]["displayMessage"]
                if TARGET_USERNAME.lower() in author.lower():
                    alert = f"🌞 {author} said: {text}"
                    print(alert)
                    send_telegram_message(alert)
            time.sleep(15)
        except Exception as e:
            print("⚠️ Error:", e)
            time.sleep(30)

if __name__ == "__main__":
    monitor()
