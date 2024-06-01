import json
import asyncio
import logging
import boto3

import utils.aws_utils as aws_utils

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from update_handler import start, event, help

### Setup Logging ###
logger = logging.getLogger("SMA Logger")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
logger.addHandler(logging.StreamHandler())
logger.handlers[0].setFormatter(formatter)

### AWS clients ###
ssm_client = boto3.client("ssm")

### Constants ###
TELEGRAM_TOKEN = aws_utils.get_parameter(
    parameter_name="/telegram/bot-token", is_secure=True, ssm_client=ssm_client
)

### Telegram bot app setup ###
app = Application.builder().token(TELEGRAM_TOKEN).build()

# Add handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help))
app.add_handler(CommandHandler("event", event))
# app.add_handler(MessageHandler(filters.TEXT & ~(filters.COMMAND), event))


async def process_update(update: Update):
    """Process a single update."""
    await app.initialize()
    await app.process_update(update)
    await app.shutdown()


def lambda_handler(event: dict, context):
    """AWS Lambda function to handle incoming webhook."""

    logger.info(f"Received event: {event}")

    update = Update.de_json(json.loads(event["body"]), app.bot)
    chat_id = update.effective_chat.id
    ALLOWED_CHAT_IDS = [
        int(chat_id)
        for chat_id in aws_utils.get_parameter(
            parameter_name="/telegram/allow-chat-ids",
            is_secure=True,
            ssm_client=ssm_client,
        ).split(",")
    ]

    if chat_id not in ALLOWED_CHAT_IDS:
        asyncio.run(update.message.reply_text("You are not allowed to use this bot"))
        return {"statusCode": 200, "body": "You are not allowed to use this bot"}

    asyncio.run(process_update(update))

    return {"statusCode": 200, "body": "Elaboration completed"}


if __name__ == "__main__":
    with open("test\\telegram_request.json", "r") as f:
        text = f.read()
    event = {"body": text}

    lambda_handler(event, None)
