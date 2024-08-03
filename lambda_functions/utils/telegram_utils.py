import asyncio
import os
import telegram
from telegram.ext import PicklePersistence
from aws_utils import get_s3_object, put_s3_object

_S3_BUCKET_CHAT_PERSISTENCE_NAME = os.environ["S3_BUCKET_CHAT_PERSISTENCE_NAME"]


def send_telegram_message(token: str, chat_id: str, message: str) -> None:
    """
    Send a message to a Telegram chat.

    ### Args ###
        `token` (str): the secretTelegram bot token
        `chat_id` (str): the chat ID where the message will be sent
        `message` (str): the message to be sent
    """
    bot = telegram.Bot(token)
    asyncio.run(bot.send_message(chat_id=chat_id, text=message))


def get_chat_persistence() -> PicklePersistence:
    """
    Get the chat persistence from S3.

    ### Returns ###
        `PicklePersistence`: the chat persistence
    """
    with open("telegram_chat_persistence", "wb") as f:
        f.write(
            get_s3_object(_S3_BUCKET_CHAT_PERSISTENCE_NAME, "telegram_chat_persistence")
        )
        return PicklePersistence(filename="telegram_chat_persistence")


def upload_chat_persistence() -> bool:
    """
    Upload the chat persistence file from local to S3.
    """
    with open("telegram_chat_persistence", "rb") as f:
        put_s3_object(
            bucket_name=_S3_BUCKET_CHAT_PERSISTENCE_NAME,
            object_key="telegram_chat_persistence",
            body=f.read(),
        )
        return True
