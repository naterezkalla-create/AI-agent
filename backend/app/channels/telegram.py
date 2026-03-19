"""Telegram bot handler with polling support."""

import logging
import asyncio
import os
from telegram import Update, Bot
from telegram.constants import ParseMode
from fastapi import APIRouter, Request
from app.core.agent import run
from app.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["telegram"])

# Global polling task
_polling_task = None


def _get_bot() -> Bot:
    settings = get_settings()
    return Bot(token=settings.telegram_bot_token)


def _get_effective_webhook_base_url() -> str:
    """Prefer explicit webhook URL, otherwise derive from Railway public domain."""
    settings = get_settings()
    if settings.telegram_webhook_url:
        return settings.telegram_webhook_url.rstrip("/")

    railway_public_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
    if railway_public_domain:
        return f"https://{railway_public_domain}"

    return ""


async def _send_telegram_text(bot: Bot, chat_id: int, text: str) -> None:
    """Send Telegram text, falling back to plain text if Markdown formatting fails."""
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception as e:
        logger.warning(f"Telegram Markdown send failed, retrying plain text: {e}")
        await bot.send_message(
            chat_id=chat_id,
            text=text,
        )


async def _handle_message(chat_id: int, user_text: str):
    """Process a message and send response."""
    user_id = f"telegram_{chat_id}"
    logger.info(f"Telegram message from {chat_id}: {user_text[:100]}")

    try:
        result = await run(
            user_message=user_text,
            user_id=user_id,
        )

        bot = _get_bot()
        # Send response, splitting if too long for Telegram (4096 char limit)
        response_text = result.text
        while response_text:
            chunk = response_text[:4000]
            response_text = response_text[4000:]
            await _send_telegram_text(bot, chat_id, chunk)

    except Exception as e:
        logger.error(f"Telegram handler error: {e}")
        bot = _get_bot()
        await bot.send_message(
            chat_id=chat_id,
            text="Sorry, something went wrong. Please try again.",
        )


@router.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """Handle incoming Telegram updates (webhook mode)."""
    settings = get_settings()

    if not settings.telegram_bot_token:
        return {"error": "Telegram bot not configured"}

    body = await request.json()
    update = Update.de_json(body, _get_bot())

    if not update.message or not update.message.text:
        return {"ok": True}

    chat_id = update.message.chat_id
    user_text = update.message.text

    await _handle_message(chat_id, user_text)
    return {"ok": True}


async def _polling_loop():
    """Start long polling for Telegram updates."""
    settings = get_settings()
    if not settings.telegram_bot_token:
        return

    bot = _get_bot()
    logger.info("Starting Telegram bot polling...")

    offset = 0
    while True:
        try:
            updates = await bot.get_updates(offset=offset, timeout=30)

            for update in updates:
                if update.message and update.message.text:
                    chat_id = update.message.chat_id
                    user_text = update.message.text
                    await _handle_message(chat_id, user_text)

                offset = update.update_id + 1

        except asyncio.CancelledError:
            logger.info("Telegram polling stopped")
            break
        except Exception as e:
            logger.error(f"Telegram polling error: {e}")
            await asyncio.sleep(5)  # Wait before retrying


async def start_polling():
    """Start Telegram polling in background."""
    global _polling_task
    settings = get_settings()

    if not settings.telegram_bot_token:
        logger.warning("Telegram not configured, skipping polling")
        return

    _polling_task = asyncio.create_task(_polling_loop())
    logger.info("Telegram polling started")


async def stop_polling():
    """Stop Telegram polling."""
    global _polling_task
    if _polling_task:
        _polling_task.cancel()
        try:
            await _polling_task
        except asyncio.CancelledError:
            pass
        _polling_task = None
        logger.info("Telegram polling stopped")


async def setup_webhook():
    """Set the Telegram webhook URL (webhook mode)."""
    settings = get_settings()
    webhook_base_url = _get_effective_webhook_base_url()

    # If webhook URL is provided or can be derived (Railway), use it; otherwise use polling
    if webhook_base_url:
        if not settings.telegram_bot_token:
            return

        bot = _get_bot()
        webhook_url = f"{webhook_base_url}/webhook/telegram"
        try:
            await bot.set_webhook(url=webhook_url)
            logger.info(f"Telegram webhook set to: {webhook_url}")
        except Exception as e:
            logger.warning(f"Failed to set Telegram webhook: {e}")
            if os.getenv("RAILWAY_PUBLIC_DOMAIN"):
                logger.warning("Running on Railway without a working webhook; skipping polling to avoid duplicate Telegram consumers.")
                return
            await start_polling()
    else:
        # Use polling for local development
        await start_polling()
