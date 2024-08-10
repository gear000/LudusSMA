import os

from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)


from utils.aws_utils import list_s3_folders, get_parameter
from .chat_state import ChatOrchestratorState
from .commands_handler import *
from .operations_handler import *

from telegram.ext import CallbackQueryHandler


### Constants ###

S3_BUCKET_IMAGES_NAME = os.environ["S3_BUCKET_IMAGES_NAME"]
TELEGRAM_TOKEN = get_parameter(parameter_name="/telegram/bot-token", is_secure=True)


def get_orchestrator_handler() -> ConversationHandler:
    """
    Returns the conversation handler for the bot.
    """

    return ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("help", help),
            CommandHandler("add_event", add_event),
            CommandHandler("delete_event", delete_event),
            CommandHandler("manage_event_images", manage_event_images),
            CommandHandler("create_story", create_story),
            CommandHandler("create_post", create_post),
        ],
        allow_reentry=True,
        states={
            ChatOrchestratorState.SELECTING_ACTION: [
                CallbackQueryHandler(selecting_action_handler)
            ],
            ChatOrchestratorState.ADD_EVENT: [add_event_handler],
        },
        fallbacks=[
            MessageHandler(filters.Regex("^Done$"), done),
            CommandHandler("done", done),
        ],
    )