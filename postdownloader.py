import os
import re
import asyncio
import requests
from flask import Flask, request
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

app = Flask(__name__)

user = TelegramClient("user_session", API_ID, API_HASH)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
user = TelegramClient("user_session", API_ID, API_HASH)
user.start()   # ✅ to‘g‘ri


def parse_link(text):
    text = text.split("?")[0].strip()

    m = re.search(r"t\.me/c/(\d+)/(\d+)", text)
    if m:
        return int("-100" + m.group(1)), int(m.group(2))

    m = re.search(r"t\.me/([A-Za-z0-9_]+)/(\d+)", text)
    if m:
        return m.group(1), int(m.group(2))

    return None, None


def send_message(chat_id, text):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": chat_id, "text": text}
    )


def send_file(chat_id, file_path, caption=""):
    with open(file_path, "rb") as f:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
            data={"chat_id": chat_id, "caption": caption[:1000]},
            files={"document": f}
        )


@app.route("/")
def home():
    return "Bot is running!"


@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()

    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    if not chat_id:
        return "ok"

    if text == "/start":
        send_message(chat_id, "Send me post link")
        return "ok"

    if "t.me/" not in text:
        return "ok"

    send_message(chat_id, "⏳ Yuklayapman...")

    channel, post_id = parse_link(text)

    if not channel:
        send_message(chat_id, "❌ Link noto‘g‘ri.")
        return "ok"

    try:
        post = loop.run_until_complete(user.get_messages(channel, ids=post_id))

        if not post:
            send_message(chat_id, "❌ Post topilmadi.")
            return "ok"

        caption = post.text or "Media"

        if post.media:
            file_path = loop.run_until_complete(
                user.download_media(post, file=DOWNLOAD_DIR)
            )
            send_file(chat_id, file_path, caption)
            os.remove(file_path)
        else:
            send_message(chat_id, caption)

    except Exception as e:
        send_message(chat_id, f"❌ Xato:\n{e}")

    return "ok"


@app.before_request
def setup_webhook_once():
    if WEBHOOK_URL:
        requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
            params={"url": f"{WEBHOOK_URL}/{BOT_TOKEN}"}
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
