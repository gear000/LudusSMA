import json
import boto3

from PIL import Image
from io import BytesIO

from utils.image_utils import image_edit
from utils.social_utils import publish_story

from utils import aws_utils  # ricordati di spostare utils in lambda_functions
# from utils.telegram_utils import send_telegram_message
# from utils.logger_utils import *


ssm_client = boto3.client("ssm")
s3_client = boto3.client("s3")


def _lambda_handler(event: dict, context):

    logger.info(f"Received event: {event}")
    logger.info(f"Received context: {context}")

    sqs_record: dict = event.get("Records")[0]
    logger.info(f"Received event: {sqs_record.get('body')}")

    event_json = json.loads(sqs_record.get("body"))

    TELEGRAM_TOKEN = aws_utils.get_parameter(
        parameter_name="/telegram/bot-token", is_secure=True
    )
    ALLOWED_CHAT_IDS = [
        int(chat_id)
        for chat_id in aws_utils.get_parameter(
            parameter_name="/telegram/allow-chat-ids",
            is_secure=True,
        ).split(",")
    ]

    send_telegram_message(
        token=TELEGRAM_TOKEN,
        chat_id=ALLOWED_CHAT_IDS[0],
        message="Una storia è stata creata su IG!\nNo, non è vero è solo un test ahah",
    )

    return {"statusCode": 200, "body": "Elaboration completed"}


def lambda_handler(event: dict, context):
    """
    

    """
    META_CLIENT_SECRET = aws_utils.get_parameter(
        parameter_name="/meta/client-secret", is_secure=True
    )

    META_ACCESS_TOKEN = aws_utils.get_parameter(
        parameter_name="/meta/access-token", is_secure=True
    )

    img_from_s3 = aws_utils.get_s3_object(
        bucket_name="ludussma-images",
        object_key="clean-images/bang-tournament/image-v1.png",
        # s3_client=s3_client,
    )
    # im = Image.open(img_from_s3)
    # im.save("test_get_image.png")
    
    print("Editing immagine in corso.")
    img_path_edit, file_name, file_stream = image_edit(img_from_s3, event)
    # ----------------------------
    # caricamento immagine su s3

    # file_stream = BytesIO()
    # im = Image.open(img_path_edit)  # Image.fromarray(img_array)
    # im.save(file_stream, format="png")

    # img_name = "test"
    aws_utils.put_s3_object(
        bucket_name="ludussma-images",
        object_key=img_path_edit,
        body=file_stream.getvalue(),
        # s3_client=s3_client,
    )
    # ----------------------------
    # generazione presigned url
    img_url = aws_utils.create_presigned_url(
        bucket_name="ludussma-images",
        object_key=f"to-upload/{file_name}",
        # s3_client=s3_client,
    )
    # ----------------------------
    print(img_url)

    # ----------------------------
    # post storia ig
    # ritornare messaggio di successo o eventuale errore
    meta_config = {
        "fb_page_id": "317629034756571",
        "ig_user_id": "17841465940733845",
        "client_id": "1816564495510379",
        "client_secret": META_CLIENT_SECRET,
        "api_version": "v19.0",
        "access_token": META_ACCESS_TOKEN,
    }
    print("Pubblicazione storia Instagram in corso.")
    publish_story(img_url, meta_config)
    # ----------------------------

    return {"statusCode": 200, "body": "Elaboration completed"}


if __name__ == "__main__":

    with open("../test/event.json") as f:
        event = json.load(f)
        lambda_handler(event, None)
