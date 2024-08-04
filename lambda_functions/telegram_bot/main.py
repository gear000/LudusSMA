import json
import asyncio
import logging
import os

from test_handler_with_state import handler_with_state
from utils.aws_utils import get_parameter, delete_message_from_sqs_queue

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from utils.telegram_utils import get_chat_persistence, upload_chat_persistence

from update_handler import start, event, help, my_event_handler

### Setup Logging ###
logger = logging.getLogger("SMA Logger")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
logger.addHandler(logging.StreamHandler())
logger.handlers[0].setFormatter(formatter)

### Constants ###
TELEGRAM_TOKEN = get_parameter(parameter_name="/telegram/bot-token", is_secure=True)


def initialize_app() -> Application:
    """
    Initialize the Telegram bot app

    ### Returns ###
    """
    chat_percistence_state = get_chat_persistence()
    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .persistence(chat_percistence_state)
        .build()
    )
    return app


async def process_update(app: Application, update: Update):
    """
    Process a single update

    ### Args ###
        `app` (Application): the Telegram bot app
        `update` (Update): the Telegram update to process
    """

    # Add handlers
    # app.add_handler(CommandHandler("start", start))
    # app.add_handler(CommandHandler("help", help))
    # app.add_handler(CommandHandler("event", event))
    # app.add_handler(MessageHandler(filters.TEXT & ~(filters.COMMAND), my_event_handler))

    app.add_handler(handler_with_state())

    await app.initialize()
    await app.process_update(update)
    await app.shutdown()

    upload_chat_persistence()


def lambda_handler(event: dict, context):
    """AWS Lambda function to handle incoming webhook."""

    sqs_record: dict = event.get("Records")[0]
    logger.info(f"Received event: {sqs_record.get('body')}")

    sqs_receipt_handle: str = sqs_record.get("receiptHandle")
    delete_message_from_sqs_queue(
        queue_name=os.getenv("SQS_QUEUE_TELEGRAM_UPDATES_NAME"),
        receipt_handle=sqs_receipt_handle,
    )

    app = initialize_app()

    update = Update.de_json(json.loads(sqs_record.get("body")), app.bot)
    chat_id = update.effective_chat.id
    ALLOWED_CHAT_IDS = [
        int(chat_id)
        for chat_id in get_parameter(
            parameter_name="/telegram/allow-chat-ids",
            is_secure=True,
        ).split(",")
    ]

    if chat_id not in ALLOWED_CHAT_IDS:
        asyncio.run(update.message.reply_text("You are not allowed to use this bot"))
        return {"statusCode": 200, "body": "You are not allowed to use this bot"}

    asyncio.run(process_update(app=app, update=update))

    return {"statusCode": 200, "body": "Elaboration completed"}


if __name__ == "__main__":
    with open("test\\telegram_request.json", "r") as f:
        text = f.read()
    event = {"body": text}

    lambda_handler(event, None)
