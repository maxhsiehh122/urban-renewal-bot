import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from telegram import Update

from bot import build_app

load_dotenv()
logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "").rstrip("/")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")

telegram_app = build_app(TOKEN)

# LINE setup
line_parser = None
line_config = None
if LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN:
    from line_bot import build_parser
    from linebot.v3.messaging import Configuration
    line_parser = build_parser(LINE_CHANNEL_SECRET)
    line_config = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
    logger.info("LINE webhook enabled")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await telegram_app.initialize()
    if WEBHOOK_URL:
        await telegram_app.bot.set_webhook(f"{WEBHOOK_URL}/webhook")
        await telegram_app.start()
        logger.info("Telegram webhook mode: %s/webhook", WEBHOOK_URL)
    else:
        await telegram_app.updater.start_polling(drop_pending_updates=True)
        await telegram_app.start()
        logger.info("Telegram polling mode")
    yield
    await telegram_app.updater.stop()
    await telegram_app.stop()
    await telegram_app.shutdown()


web_app = FastAPI(lifespan=lifespan)


@web_app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}


@web_app.post("/line-webhook")
async def line_webhook(request: Request):
    if not line_parser:
        raise HTTPException(status_code=503, detail="LINE not configured")

    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()

    from linebot.v3.exceptions import InvalidSignatureError
    from linebot.v3.webhooks import MessageEvent, TextMessageContent
    from line_bot import handle_event
    import asyncio

    try:
        events = line_parser.parse(body.decode(), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # 先回 200，背景處理查詢（LINE 要求 1 秒內回應）
    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
            asyncio.create_task(handle_event(event, line_config))

    return {"ok": True}


@web_app.get("/")
async def health():
    return {"status": "ok", "telegram": "webhook" if WEBHOOK_URL else "polling", "line": bool(line_parser)}
