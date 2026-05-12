import logging
import os
import re

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from formatter import format_error, format_no_result, format_results
from querier import query_by_address, split_cases

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

ADDRESS_PATTERN = re.compile(r"[路街道巷弄號]")

WELCOME = (
    "👋 *都更查詢機器人*\n\n"
    "輸入台北市地址，查詢是否有都更申請及目前進度。\n\n"
    "📌 *格式範例*\n"
    "• `和平東路一段100號`\n"
    "• `大安區忠孝東路四段1號`\n"
    "• `台北市信義區松仁路1號`\n\n"
    "資料來源：臺北市都市更新審議服務平台"
)

HELP = (
    "📖 *使用說明*\n\n"
    "直接輸入台北市地址即可查詢。\n\n"
    "查詢結果說明：\n"
    "🔴 進行中案件 — 目前有都更審議程序\n"
    "📋 歷史案件 — 過去曾申請但已結案\n"
    "✅ 查無案件 — 目前無都更記錄\n\n"
    "⚠️ 目前僅支援台北市地址"
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME, parse_mode=ParseMode.MARKDOWN)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP, parse_mode=ParseMode.MARKDOWN)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    address = update.message.text.strip()

    if not ADDRESS_PATTERN.search(address):
        await update.message.reply_text(
            "⚠️ 請輸入完整地址（需含路名及號碼）\n範例：`和平東路一段100號`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    from querier import _cache
    import time
    cached = address in _cache and (time.monotonic() - _cache[address][1]) < 3600

    if not cached:
        await update.message.reply_text("⏳ 查詢中，請稍候…")

    try:
        cases = await query_by_address(address)
    except Exception as e:
        logger.error("Query failed for %s: %s", address, e)
        await update.message.reply_text(format_error())
        return

    if not cases:
        await update.message.reply_text(format_no_result(address))
        return

    active, historical = split_cases(cases)
    reply = format_results(address, active, historical)
    await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)


def build_app(token: str) -> Application:
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app
