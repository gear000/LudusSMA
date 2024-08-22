import asyncio
import os
import telegram

from .logger_utils import *
from .aws_utils import get_parameter, get_s3_object, put_s3_object

from telegram.ext import PicklePersistence, Application

TELEGRAM_TOKEN = get_parameter(parameter_name="/telegram/bot-token", is_secure=True)
_S3_BUCKET_CHAT_PERSISTENCE_NAME = os.getenv("S3_BUCKET_CHAT_PERSISTENCE_NAME")
_CHAT_PERSISTENCE_STATE = "telegram_chat_persistence_state"


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


def get_chat_persistence(chat_id: str) -> PicklePersistence:
    """
    Get the chat persistence from S3.

    ### Returns ###
        `PicklePersistence`: the chat persistence
    """
    try:
        telegram_chat_persistence_state = get_s3_object(
            _S3_BUCKET_CHAT_PERSISTENCE_NAME,
            "/".join([chat_id, _CHAT_PERSISTENCE_STATE]),
        ).read()
        with open(f"/tmp/{_CHAT_PERSISTENCE_STATE}", "wb") as f:
            f.write(telegram_chat_persistence_state)
    except AttributeError:
        logger.error("Telegram chat persistence not found. Creating new one.")

    return PicklePersistence(filepath=f"/tmp/{_CHAT_PERSISTENCE_STATE}")


def upload_chat_persistence(chat_id: str) -> bool:
    """
    Upload the chat persistence file from local to S3.
    """
    with open(f"/tmp/{_CHAT_PERSISTENCE_STATE}", "rb") as f:
        put_s3_object(
            bucket_name=_S3_BUCKET_CHAT_PERSISTENCE_NAME,
            object_key="/".join([chat_id, _CHAT_PERSISTENCE_STATE]),
            body=f.read(),
        )
        return True


def initialize_app(chat_id: str = "default") -> Application:
    """
    Initialize the Telegram bot app
    """
    chat_percistence_state = get_chat_persistence(chat_id)
    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .persistence(chat_percistence_state)
        .build()
    )
    return app
