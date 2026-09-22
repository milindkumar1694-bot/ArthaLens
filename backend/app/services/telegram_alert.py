import logging
import httpx
from app.config import Settings

logger = logging.getLogger("arthalens.telegram")

class TelegramAlertService:
    def __init__(self, settings: Settings):
        self.bot_token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id

    async def send_alert(self, title: str, message: str, level: str = "HIGH") -> bool:
        if not self.bot_token or not self.chat_id:
            logger.info(f"[Telegram Placeholder] ({level}) {title}: {message}")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        text = f"🚨 *ArthaLens Alert [{level}]*\n*Title*: {title}\n{message}"

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(url, json={"chat_id": self.chat_id, "text": text, "parse_mode": "Markdown"})
                return resp.status_code == 200
        except Exception as err:
            logger.error(f"Telegram dispatch failed: {err}")
            return False
