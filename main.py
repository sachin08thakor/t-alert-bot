import os
import time
import requests
from googleapiclient.discovery import build

# 🔹 Environment variables
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")
TARGET_USER = os.getenv("TARGET_USER", "Sunshine 🌞")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 🔹 Setup YouTube API client
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# ✅ Function to send Telegram alert
def send_telegram_notification(message: str):
    if not message.strip():
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Telegram error:", e)

# ✅ Get live video IDs from the channel
def get_live_video_ids():
    response = youtube.search().list(
        part="id",
        channelId=CHANNEL_ID,
        eventType="live",
        type="video",
        maxResults=5
    ).execute()

    videos = [item["id"]["videoId"] for item in response.get("items", [])]
    return videos

# ✅ Get the live chat ID from a video
def get_live_chat_id(video_id):
    response = youtube.videos().list(
        part="liveStreamingDetails",
        id=video_id
    ).execute()

    items = response.get("items", [])
    if not items:
        return None
    return items[0]["liveStreamingDetails"].get("activeLiveChatId")

# ✅ Watch live chat for target user
def monitor_chat(chat_id):
    next_page_token = None
    while True:
        try:
            chat = youtube.liveChatMessages().list(
                liveChatId=chat_id,
                part="snippet,authorDetails",
                pageToken=next_page_token
            ).execute()

            for msg in chat.get("items", []):
                author = msg["authorDetails"]["displayName"]
                text = msg["snippet"]["displayMessage"]
                if author.lower() == TARGET_USER.lower():
                    alert = f"🌞 {author} just chatted:\n{text}"
                    print(alert)
                    send_telegram_notification(alert)

            next_page_token = chat.get("nextPageToken")
            time.sleep(5)
        except Exception as e:
            print("Chat monitor error:", e)
            time.sleep(10)

# ✅ Main loop (handles multiple live streams)
def main():
    print("🔍 Searching for live streams...")
    while True:
        videos = get_live_video_ids()
        if not videos:
            print("❌ No live videos right now. Checking again in 60s...")
            time.sleep(60)
            continue

        for vid in videos:
            print(f"🎥 Found live video: {vid}")
            chat_id = get_live_chat_id(vid)
            if chat_id:
                print(f"💬 Monitoring live chat {chat_id} for '{TARGET_USER}'...")
                monitor_chat(chat_id)
            else:
                print(f"⚠️ No active chat found for video {vid}")

        time.sleep(60)

if __name__ == "__main__":
    main()
