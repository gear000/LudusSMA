import asyncio
import json
import os

from telegram import Update
from telegram.ext import Application

from utils.logger_utils import *
from utils.aws_utils import get_parameter, delete_message_from_sqs_queue
from utils.telegram_utils import get_chat_persistence, upload_chat_persistence

from .handlers.orchestrator_handler import get_orchestrator_handler


### Constants ###

S3_BUCKET_IMAGES_NAME = os.environ["S3_BUCKET_IMAGES_NAME"]
TELEGRAM_TOKEN = get_parameter(parameter_name="/telegram/bot-token", is_secure=True)


def initialize_app() -> Application:
    """
    Initialize the Telegram bot app
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

    app.add_handler(get_orchestrator_handler())
    asyncio.run(process_update(app=app, update=update))

    return {"statusCode": 200, "body": "Elaboration completed"}


if __name__ == "__main__":
    import langchain

    langchain.debug = True
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(get_orchestrator_handler())
    app.run_polling(allowed_updates=Update.ALL_TYPES)
