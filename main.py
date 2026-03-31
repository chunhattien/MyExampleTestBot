import os
import asyncio
import logging
import tempfile
from fastapi import FastAPI
import uvicorn
import httpx

from telethon import TelegramClient, events

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/")
async def home():
    return {"status": "running"}

# ================= ENV =================
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
DEST_CHAT = os.environ["DEST_CHAT"]
ALLOWED = os.environ.get("ALLOWED_USER")

try:
    DEST_CHAT = int(DEST_CHAT)
except:
    pass

pending_albums = {}

# ================= BOT =================

async def run_bot():

    while True:

        try:
            client = TelegramClient("bot_session", API_ID, API_HASH)
            await client.start(bot_token=BOT_TOKEN)

            dest = await client.get_entity(DEST_CHAT)

            logger.info("✅ Bot started")

            @client.on(events.NewMessage)
            async def handler(event):

                msg = event.message

                if ALLOWED and str(msg.sender_id) != ALLOWED:
                    return

                if msg.text and not msg.media:
                    await client.send_message(dest, msg.text)
                    return

                if msg.media:
                    path = await msg.download_media(
                        file=tempfile.NamedTemporaryFile(delete=False).name
                    )
                    await client.send_file(dest, path)

            await client.run_until_disconnected()

        except Exception:
            logger.exception("Bot crashed → restart sau 10s")
            await asyncio.sleep(10)

# ================= KEEP ALIVE =================

async def self_ping():
    url = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:10000")
    while True:
        try:
            await httpx.get(url)
        except:
            pass
        await asyncio.sleep(300)

# ================= START =================

@app.on_event("startup")
async def startup():
    asyncio.create_task(run_bot())
    asyncio.create_task(self_ping())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
