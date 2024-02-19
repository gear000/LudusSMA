import logging
import os
from dotenv import load_dotenv

from telegram.ext import Application, CommandHandler

logger = logging.getLogger("SMA Logger")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
logger.addHandler(logging.StreamHandler())
logger.handlers[0].setFormatter(formatter)
logger.info("Starting SMA Bot")

load_dotenv()


async def start(update, context):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Ciao! Sono il tuo bot."
    )


async def test_2(update, context):

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Ciao! Questo è un test!"
    )


def main():
    TOKEN = os.getenv("telegram_token")
    if TOKEN is None:
        raise Exception("Telegram token not found")

    application = Application.builder().token(TOKEN).build()

    start_handler = CommandHandler("start", start)
    test_handler = CommandHandler("test", test_2)
    application.add_handler(start_handler)
    application.add_handler(test_handler)

    application.run_polling()


if __name__ == "__main__":
    main()
