"""
Entry point.
- Development: polling mode (python main.py)
- Production:  webhook mode via FastAPI (uvicorn main:web_app)
"""

import logging
import os

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "").rstrip("/")
PORT = int(os.environ.get("PORT", 8000))

logger = logging.getLogger(__name__)

# ── Webhook mode (production on Render) ──────────────────────────────────────
if WEBHOOK_URL:
    from contextlib import asynccontextmanager

    from fastapi import FastAPI, Request
    from telegram import Update

    from bot import build_app

    telegram_app = build_app(TOKEN)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await telegram_app.initialize()
        await telegram_app.bot.set_webhook(f"{WEBHOOK_URL}/webhook")
        await telegram_app.start()
        logger.info("Webhook set to %s/webhook", WEBHOOK_URL)
        yield
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
        return {"status": "ok", "mode": "webhook"}

# ── Polling mode (local development) ─────────────────────────────────────────
else:
    from bot import build_app

    def run_polling():
        app = build_app(TOKEN)
        logger.info("Starting polling mode…")
        app.run_polling(drop_pending_updates=True)

    if __name__ == "__main__":
        run_polling()
