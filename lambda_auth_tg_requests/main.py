import imp
import logging
import os

import utils.aws_utils as aws_utils
from utils.logger_utils import *


def lambda_handler(event: dict, context):
    """AWS Lambda function to handle incoming webhook."""

    SECRET_TOKEN = aws_utils.get_parameter(
        parameter_name=os.getenv("TELEGRAM_HEADER_WEBHOOK_TOKEN"), is_secure=True
    )

    headers: dict = event.get("headers", {})
    client_secret = headers.get("X-Telegram-Bot-Api-Secret-Token", "")

    if client_secret != SECRET_TOKEN:
        return {"statusCode": 401, "body": "Unauthorized"}
    else:

        aws_utils.send_message_in_sqs_queue(
            queue_name=os.getenv("SQS_QUEUE_TELEGRAM_UPDATES_NAME"),
            message=event.get("body", {}),
        )

    return {"statusCode": 202, "body": "Accepted"}