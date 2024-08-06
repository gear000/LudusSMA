import os

from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)


from utils.aws_utils import list_s3_folders, get_parameter
from .update_handler import (
    ChatState,
    done,
    choose_event_type,
    start,
    help,
    event,
    media_handler,
    add_image_first,
    llm_processing,
    schedule_event,
)


### Constants ###

S3_BUCKET_IMAGES_NAME = os.environ["S3_BUCKET_IMAGES_NAME"]
TELEGRAM_TOKEN = get_parameter(parameter_name="/telegram/bot-token", is_secure=True)


def get_conversation_handler() -> ConversationHandler:
    """
    Returns the conversation handler for the bot.
    """

    event_types = [
        elem.strip("/").split("/")[-1].title()
        for elem in list_s3_folders(S3_BUCKET_IMAGES_NAME, "clean-images/")
    ]

    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ChatState.INTRO: [
                MessageHandler(
                    filters.Regex("^Aggiungere un evento$"),
                    choose_event_type,
                ),
                MessageHandler(
                    filters.Regex("^Caricare un'immagine$"),
                    media_handler,
                ),
            ],
            ChatState.ADD_EVENT: [
                MessageHandler(filters.Regex(f"^{'|'.join(event_types)}$"), event),
                MessageHandler(filters.Regex(f"^Altro$"), add_image_first),
            ],
            ChatState.EVENT_INFO: [
                MessageHandler(filters.TEXT & ~(filters.COMMAND), llm_processing)
            ],
            ChatState.RECAP: [
                MessageHandler(
                    filters.Regex("^Vai con l'evento!$"),
                    schedule_event,
                ),
                MessageHandler(
                    filters.Regex("^No, aspetta...$"),
                    event,
                ),
            ],
        },
        fallbacks=[
            MessageHandler(filters.Regex("^Done$"), done),
            CommandHandler("done", done),
        ],
    )
