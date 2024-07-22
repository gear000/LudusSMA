import json
import asyncio
import logging
import os
import boto3

from utils import aws_utils

from telegram import Update, Bot
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

bot = Bot(token=TELEGRAM_TOKEN)
asyncio.run(bot.send_message(chat_id=143243107, text="Hello World"))
