import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from telegram import Update

from bot import build_app

load_dotenv()
logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "").rstrip("/")

telegram_app = build_app(TOKEN)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await telegram_app.initialize()
    if WEBHOOK_URL:
        await telegram_app.bot.set_webhook(f"{WEBHOOK_URL}/webhook")
        await telegram_app.start()
        logger.info("Webhook mode: %s/webhook", WEBHOOK_URL)
    else:
        await telegram_app.updater.start_polling(drop_pending_updates=True)
        await telegram_app.start()
        logger.info("Polling mode (no WEBHOOK_URL set)")
    yield
    await telegram_app.updater.stop()
    await telegram_app.stop()
    await telegram_app.shutdown()


web_app = FastAPI(lifespan=lifespan)


@web_app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}


@web_app.get("/")
async def health():
    return {"status": "ok", "mode": "webhook" if WEBHOOK_URL else "polling"}
