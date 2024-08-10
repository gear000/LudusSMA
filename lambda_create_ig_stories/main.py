from utils import aws_utils  # ricordati di spostare utils in lambda_functions
from utils.telegram_utils import send_telegram_message
import boto3
from image_editing import image_edit
from imgur_functions import load_imgur
from meta_functions import publish_story
from PIL import Image
from io import BytesIO

ssm_client = boto3.client("ssm")
s3_client = boto3.client("s3")


def lambda_handler(event, context):
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


def _lambda_handler(event: dict, context):
    """
    event = {"event_id": "1234567890"}

    """
    META_CLIENT_SECRET = aws_utils.get_parameter(
        parameter_name="/meta/client-secret", is_secure=True, ssm_client=ssm_client
    )

    META_ACCESS_TOKEN = aws_utils.get_parameter(
        parameter_name="/meta/access-token", is_secure=True, ssm_client=ssm_client
    )

    # fare 3 metodi
    # - get_object -> def get_s3_object
    # - put_object -> def put_s3_object wrappare le funzioni
    # - creare funzione che restituisce presigned url -> def create_presigned_url()

    img_from_s3 = aws_utils.get_s3_object(
        bucket_name="ludussma-images",
        object_key="clean-images/bang-tournament/image-v1.png",
        s3_client=s3_client,
    )
    im = Image.open(img_from_s3)
    im.save("test_get_image.png")

    # ----------------------------
    # prendere da dynamo la riga corrispondente a event_id
    # event_info = {}
    # ----------------------------

    # ----------------------------
    # generazione immagine
    # salvataggio immagine su img_path
    # ----------------------------

    # ----------------------------
    # edit immagine con testo
    # crop to aspect ratio 9:16
    # salvataggio immagine su img_path_edit

    # provare su aws s3 a caricare un file e creare un url presigned

    # EVENT_TYPE = {
    #     ""
    # }

    # img_path = "bang.png"
    img_path = "test_get_image.png"

    edit_dict = {
        "title": {"text": "Torneo di Bang", "size": 70, "anchor": "mm"},
        "description": {
            "text": "Divertiti con noi al più famoso gioco western!",
            "size": 40,
            "anchor": "mm",
        },
        "date": {"text": "Mercoledì 31 febbraio", "size": 40, "anchor": "lm"},
        "time": {"text": "21:00", "size": 40, "anchor": "lm"},
        "location": {"text": "Centro NOI di Povegliano", "size": 40, "anchor": "lm"},
        "cost": {"text": "Iscrizione libera", "size": 40, "anchor": "lm"},
        # "other_info": se non ci sono "na"
    }
    print("Editing immagine in corso.")
    img_path_edit = image_edit(img_path, edit_dict)
    # ----------------------------
    # caricamento immagine su s3

    file_stream = BytesIO()
    im = Image.open(img_path_edit)  # Image.fromarray(img_array)
    im.save(file_stream, format="png")

    img_name = "test"
    aws_utils.put_s3_object(
        bucket_name="ludussma-images",
        object_key=f"to-upload/{img_name}.png",
        body=file_stream.getvalue(),
        s3_client=s3_client,
    )
    # ----------------------------
    # generazione presigned url
    img_url = aws_utils.create_presigned_url(
        bucket_name="ludussma-images",
        object_key=f"to-upload/{img_name}.png",
        s3_client=s3_client,
    )
    # ----------------------------

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

    lambda_handler(1, 2)
