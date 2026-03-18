"""Telegram bot handler with polling support."""

import logging
import asyncio
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
            await bot.send_message(
                chat_id=chat_id,
                text=chunk,
                parse_mode=ParseMode.MARKDOWN,
            )

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

    # If webhook URL is provided, use it; otherwise use polling
    if settings.telegram_webhook_url:
        if not settings.telegram_bot_token:
            return

        bot = _get_bot()
        webhook_url = f"{settings.telegram_webhook_url}/webhook/telegram"
        try:
            await bot.set_webhook(url=webhook_url)
            logger.info(f"Telegram webhook set to: {webhook_url}")
        except Exception as e:
            logger.warning(f"Failed to set webhook, falling back to polling: {e}")
            await start_polling()
    else:
        # Use polling for local development
        await start_polling()
