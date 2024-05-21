import json
import asyncio
import logging
import boto3

import utils.aws_utils as aws_utils

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from update_handler import start, event

### Setup Logging ###
logger = logging.getLogger("SMA Logger")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
logger.addHandler(logging.StreamHandler())
logger.handlers[0].setFormatter(formatter)

### AWS clients ###
ssm_client = boto3.client("ssm")

### Constants ###
TELEGRAM_TOKEN = aws_utils.get_parameters(
    parameter_name="/telegram/bot-token", is_secure=True, ssm_client=ssm_client
)

### Telegram bot app setup ###
app = Application.builder().token(TELEGRAM_TOKEN).build()

# Add handlers
app.add_handler(CommandHandler("event", start))
app.add_handler(MessageHandler(filters.TEXT & ~(filters.COMMAND), event))


async def process_update(update: Update):
    """Process a single update."""
    await app.initialize()
    await app.process_update(update)
    await app.shutdown()


def lambda_handler(event: dict, context):
    """AWS Lambda function to handle incoming webhook."""

    SECRET_TOKEN = aws_utils.get_parameters(
        parameter_name="/telegram/header-webhook-token",
        is_secure=True,
        ssm_client=ssm_client,
    )

    headers: dict = event.get("headers", {})
    client_secret = headers.get("X-Telegram-Bot-Api-Secret-Token", "")

    if client_secret != SECRET_TOKEN:
        return {"statusCode": 401, "body": "Unauthorized"}

    update = Update.de_json(json.loads(event["body"]), app.bot)
    chat_id = update.effective_chat.id
    ALLOWED_CHAT_IDS = [
        int(chat_id)
        for chat_id in aws_utils.get_parameters(
            parameter_name="/telegram/allow-chat-ids",
            is_secure=True,
            ssm_client=ssm_client,
        ).split(",")
    ]

    if chat_id not in ALLOWED_CHAT_IDS:
        asyncio.run(update.message.reply_text("You are not allowed to use this bot"))
        return {"statusCode": 200, "body": "You are not allowed to use this bot"}

    logger.info(f"Received update: {update}")
    asyncio.run(process_update(update))

    return {"statusCode": 200, "body": "Elaboration completed"}
