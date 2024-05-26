import logging
import os
import boto3

import utils.aws_utils as aws_utils

### Setup Logging ###
logger = logging.getLogger("Auth Tg Request Logger")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
logger.addHandler(logging.StreamHandler())
logger.handlers[0].setFormatter(formatter)

### AWS clients ###
ssm_client = boto3.client("ssm")
sqs_client = boto3.client("sqs")


def lambda_handler(event: dict, context):
    """AWS Lambda function to handle incoming webhook."""

    logger.info(f"Received event: {event}")

    SECRET_TOKEN = aws_utils.get_parameter(
        parameter_name=os.getenv("TELEGRAM_HEADER_WEBHOOK_TOKEN"),
        is_secure=True,
        ssm_client=ssm_client,
    )

    headers: dict = event.get("headers", {})
    client_secret = headers.get("X-Telegram-Bot-Api-Secret-Token", "")

    if client_secret != SECRET_TOKEN:
        return {"statusCode": 401, "body": "Unauthorized"}

    return {"statusCode": 202, "body": "Accepted"}
