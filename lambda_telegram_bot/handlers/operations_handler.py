from datetime import date
from enum import Enum
import os
import telegram

from telegram.constants import ParseMode

from telegram import (
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from utils.models.model_utils import OutputCreateEvent

from chatbot.tools import create_schedulers
from chatbot.event_handler import check_info_chain

from .chat_state import ChatOrchestratorState, ChatAddEventState
from .commands_handler import *

__all__ = [
    "selecting_action_handler",
    "add_event_handler",
    "delete_event_handler",
    "manage_event_images_handler",
    "create_story_handler",
    "create_post_handler",
]


DYNAMODB_TABLE_CHATS_HISTORY_NAME = os.environ["DYNAMODB_TABLE_CHATS_HISTORY_NAME"]


async def done(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End the conversation."""

    await update.message.reply_text(
        f"Lieto di esserti stato utile!",
        reply_markup=ReplyKeyboardRemove(),
    )

    context.user_data.clear()
    return ConversationHandler.END


async def selecting_action_handler(
    update: telegram.Update, context: ContextTypes.DEFAULT_TYPE
):
    state = int(update.callback_query.data)
    match ChatOrchestratorState(state):
        case ChatOrchestratorState.ADD_EVENT:
            return await add_event(update, context)
        case ChatOrchestratorState.DELETE_EVENT:
            return await delete_event(update, context)
        case ChatOrchestratorState.MANAGE_EVENT_IMAGES:
            return await manage_event_images(update, context)
        case ChatOrchestratorState.CREATE_STORY:
            return await create_story(update, context)
        case ChatOrchestratorState.CREATE_POST:
            return await create_post(update, context)

    raise ValueError("State not found")


# region Add Event


class ContextKeys(Enum):
    EVENT_TYPE = "Tipo di evento"
    EVENT = "Informazioni sull'evento"
    CONTEXT = "Messaggi dell'utente"
    START_OVER = "Start Over"
    EVENT_TYPE_DICT = "Dizionario degli eventi disponibili"


async def set_event(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.user_data.get(ContextKeys.EVENT_TYPE):
        text = update.callback_query.data
        context.user_data[ContextKeys.EVENT_TYPE] = text
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "Perfetto! 😊\n"
            "Per creare un evento ho bisogno di queste info:\n"
            "  - il nome dell'evento;\n"
            "  - una descrizione dell'evento;\n"
            "  - quando sarà l'evento, cioè, data e ora di inizio e data e ora di fine;\n"
            "  - dove si terrà l'evento, cioè il nome del posto o l'indirizzo.",
            reply_markup=InlineKeyboardMarkup([[]]),
        )
    else:
        await update.message.reply_text(
            "Va bene, che informazione vuoi darmi?",
            reply_markup=ReplyKeyboardRemove(),
        )

    return ChatAddEventState.EVENT_INFO


async def llm_processing(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Instantiate the bot and get the answer
    """
    text = update.message.text

    if context.user_data.get(ContextKeys.CONTEXT):
        context.user_data[ContextKeys.CONTEXT] += "\nAlice: " + text
    else:
        context.user_data[ContextKeys.CONTEXT] = "Alice: " + text

    response: OutputCreateEvent = check_info_chain.invoke(
        {"input": context.user_data[ContextKeys.CONTEXT], "today": date.today()}
    )
    clarification = response.clarification
    if clarification:
        await update.message.reply_text(
            "Mmhh, qualcosa non va...\n" + clarification,
            reply_markup=ReplyKeyboardRemove(),
        )
        context.user_data[ContextKeys.CONTEXT] += "\nBob: " + clarification
        return ChatAddEventState.EVENT_INFO
    else:

        await update.message.reply_text(
            "Bene, allora creo un evento con queste informazioni:"
            + response.event.format_for_tg_message(),
            parse_mode=ParseMode.HTML,
        )
        context.user_data[ContextKeys.EVENT] = response.event
        markup = ReplyKeyboardMarkup([["Vai con l'evento!", "No, aspetta..."]])
        await update.message.reply_text("Cosa facciamo?", reply_markup=markup)

        return ChatAddEventState.RECAP


async def schedule_event(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    """Add event in scheduler"""

    create_schedulers(context.user_data[ContextKeys.EVENT])

    await update.message.reply_text(
        f"Ho creato l'evento!",
    )
    await done(update, context)

    context.user_data.clear()
    return ConversationHandler.END


add_event_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(set_event)],
    name="add_event",
    persistent=True,
    states={
        ChatAddEventState.EVENT_INFO: [
            MessageHandler(filters.TEXT & ~(filters.COMMAND), llm_processing)
        ],
        ChatAddEventState.RECAP: [
            MessageHandler(
                filters.Regex("^Vai con l'evento!$"),
                schedule_event,
            ),
            MessageHandler(
                filters.Regex("^No, aspetta...$"),
                set_event,
            ),
        ],
    },
    fallbacks=[
        MessageHandler(filters.Regex("^Done$"), done),
        CommandHandler("done", done),
    ],
)

# endregion

# region Other Operations

delete_event_handler = ConversationHandler(entry_points=[], states={}, fallbacks=[])
manage_event_images_handler = ConversationHandler(
    entry_points=[], states={}, fallbacks=[]
)
create_story_handler = ConversationHandler(entry_points=[], states={}, fallbacks=[])
create_post_handler = ConversationHandler(entry_points=[], states={}, fallbacks=[])

# endregion
