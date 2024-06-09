import asyncio
import telegram


def send_telegram_message(token: str, chat_id: str, message: str) -> None:
    bot = telegram.Bot(token)
    asyncio.run(bot.send_message(chat_id=chat_id, text=message))
