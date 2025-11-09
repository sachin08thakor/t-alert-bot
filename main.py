from googleapiclient.discovery import build
import time
import requests
import os

# === Configuration from Railway variables ===
API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Channel ID, not video ID
TARGET_USER = os.getenv("TARGET_USER", "Sunshine 🌞")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

youtube = build("youtube", "v3", developerKey=API_KEY)


# --- Get all currently live videos on a channel ---
def get_all_live_videos(channel_id):
    res = youtube.search().list(
        part="id",
        channelId=channel_id,
        eventType="live",
        type="video",
        maxResults=5
    ).execute()
    return [item["id"]["videoId"] for item in res.get("items", [])]


# --- Get live chat ID from a video ID ---
def get_live_chat_id(video_id):
    res = youtube.videos().list(part="liveStreamingDetails", id=video_id).execute()
    items = res.get("items", [])
    if not items or "liveStreamingDetails" not in items[0]:
        return None
    return items[0]["liveStreamingDetails"].get("activeLiveChatId")


# --- Watch messages in one live chat ---
def check_messages(chat_id, video_id, token=None):
    try:
        response = youtube.liveChatMessages().list(
            liveChatId=chat_id,
            part="snippet,authorDetails",
            pageToken=token
        ).execute()

        for msg in response.get("items", []):
            name = msg["authorDetails"]["displayName"]
            text = msg["snippet"]["displayMessage"]
            if name.strip().lower() == TARGET_USER.lower():
                alert = f"☀️ Sunshine 🌞 just chatted in video {video_id}: {text}"
                print(alert)
                if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
                    requests.get(
                        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                        params={"chat_id": TELEGRAM_CHAT_ID, "text": alert}
                    )

        return response.get("nextPageToken")
    except Exception as e:
        print(f"⚠️ Error checking chat for video {video_id}: {e}")
        return None


# --- Main loop ---
print("🔍 Bot started. Watching channel for live streams...")
seen_videos = set()

while True:
    live_videos = get_all_live_videos(CHANNEL_ID)
    if not live_videos:
        print("⏳ No live streams currently running.")
        time.sleep(60)
        continue

    for vid in live_videos:
        if vid not in seen_videos:
            print(f"🎥 Found live video: {vid}")
            seen_videos.add(vid)

        chat_id = get_live_chat_id(vid)
        if chat_id:
            token = None
            token = check_messages(chat_id, vid, token)
        else:
            print(f"⚠️ No active chat for {vid}")

    time.sleep(10)
