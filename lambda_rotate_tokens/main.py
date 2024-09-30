import json
import os
import secrets
import string
import requests

from utils.aws_utils import get_parameter, set_parameter
from utils.logger_utils import *

telegram_bot_token_key = os.environ["TELEGRAM_BOT_KEY"]
telegram_header_token_key = os.environ["TELEGRAM_HEADER_WEBHOOK_TOKEN"]
telegram_bot_webhook_url = os.environ["TELEGRAM_BOT_WEBHOOK_URL"]


def _generate_random_string(length):
    if length < 1 or length > 256:
        raise ValueError("Length must be between 1 and 256")

    allowed_chars = string.ascii_letters + string.digits + "_-"
    return "".join(secrets.choice(allowed_chars) for _ in range(length))


def rotate_meta_token(): ...


def rotate_telegram_header_token():
    """Rotate Telegram Header token."""
    telegram_bot_token_value = get_parameter(
        parameter_name=telegram_bot_token_key, is_secure=True
    )
    new_telegram_header_token = _generate_random_string(256)

    url = f"https://api.telegram.org/bot{telegram_bot_token_value}/setWebhook"

    payload = {
        "url": "https://lhylsph5r3zzcdoka5twz7r6du0uedct.lambda-url.eu-west-1.on.aws/",
        "max_connections": 10,
        "allowed_updates": "message",
        "drop_pending_updates": True,
        "secret_token": new_telegram_header_token,
    }

    telegram_response = requests.request(
        method="POST", url=url, data=json.dumps(payload)
    )

    if telegram_response.status_code == 200:
        logger.info("Telegram Header token rotated successfully on Telegram side.")
        logger.info(f"Response: {telegram_response.text}")
    else:
        logger.error(
            f"Failed to rotate Telegram Header token. Status code: {telegram_response.status_code}"
        )
        raise Exception("Failed to rotate Telegram Header token.")
    set_parameter(
        parameter_name=telegram_header_token_key,
        parameter_value=new_telegram_header_token,
        parameter_type="SecureString",
    )
    logger.info("Telegram Header token rotated successfully on Systems Manager side.")


def lambda_handler(event: dict, context):
    """AWS Lambda function to rotate Meta and Telegram Header tokens."""

    rotate_telegram_header_token()

    return {"statusCode": 200, "body": "OK"}
