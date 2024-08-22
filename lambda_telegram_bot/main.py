import asyncio
import json
import os

from telegram import Update
from telegram.ext import Application

from utils.logger_utils import *
from utils.aws_utils import get_parameter, delete_message_from_sqs_queue
from utils.telegram_utils import (
    initialize_app,
    upload_chat_persistence,
)

from handlers.orchestrator_handler import get_orchestrator_handler
from handlers.operations_handler import error_handler


### Constants ###

S3_BUCKET_IMAGES_NAME = os.environ["S3_BUCKET_IMAGES_NAME"]


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

    upload_chat_persistence(str(update.effective_chat.id))


def lambda_handler(event: dict, context):
    """AWS Lambda function to handle incoming webhook."""

    sqs_record: dict = event.get("Records")[0]
    logger.info(f"Received event: {sqs_record.get('body')}")

    update = Update.de_json(json.loads(sqs_record.get("body")))
    chat_id = update.effective_chat.id

    app = initialize_app(str(chat_id))
    update.effective_chat.set_bot(app.bot)

    try:
        logger.info(f"Is bot well set?: {update.message.get_bot()}")
    except RuntimeError:
        logger.error("Bot is not set")
        return {"statusCode": 200, "body": "Bot is not set"}

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
    # app.add_error_handler(error_handler)
    asyncio.run(process_update(app=app, update=update))

    return {"statusCode": 200, "body": "Elaboration completed"}


if __name__ == "__main__":
    import langchain
    from telegram.ext import PicklePersistence

    langchain.debug = True

    TELEGRAM_TOKEN = get_parameter(parameter_name="/telegram/bot-token", is_secure=True)

    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .persistence(PicklePersistence(filepath="telegram_chat_persistence_state"))
        .build()
    )
    app.add_handler(get_orchestrator_handler())
    app.add_error_handler(error_handler)
    app.run_polling(allowed_updates=Update.ALL_TYPES)
