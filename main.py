from googleapiclient.discovery import build
import time
import requests
import os

API_KEY = os.getenv("YOUTUBE_API_KEY")
VIDEO_ID = os.getenv("VIDEO_ID")
TARGET_USER = os.getenv("TARGET_USER")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

youtube = build("youtube", "v3", developerKey=API_KEY)

def get_live_chat_id(video_id):
    res = youtube.videos().list(part="liveStreamingDetails", id=video_id).execute()
    return res["items"][0]["liveStreamingDetails"]["activeLiveChatId"]

def check_messages(chat_id, token=None):
    response = youtube.liveChatMessages().list(
        liveChatId=chat_id,
        part="snippet,authorDetails",
        pageToken=token
    ).execute()
    for msg in response["items"]:
        name = msg["authorDetails"]["displayName"]
        if name.strip().lower() == TARGET_USER.lower():
            text = msg["snippet"]["displayMessage"]
            alert = f"☀️ Sunshine 🌞 just chatted: {text}"
            print(alert)
            if TELEGRAM_BOT_TOKEN:
                requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                             params={"chat_id": CHAT_ID, "text": alert})
    return response.get("nextPageToken")

chat_id = get_live_chat_id(VIDEO_ID)
token = None
while True:
    token = check_messages(chat_id, token)
    time.sleep(5)
