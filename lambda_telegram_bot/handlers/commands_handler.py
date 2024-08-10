from email import message
import os
import telegram
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler

from utils.aws_utils import list_s3_folders
from .chat_state import ChatOrchestratorState

__all__ = [
    "start",
    "help",
    "add_event",
    "delete_event",
    "manage_event_images",
    "create_story",
    "create_post",
    "done",
]

S3_BUCKET_IMAGES_NAME = os.environ["S3_BUCKET_IMAGES_NAME"]


async def start(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the conversation and ask user for input."""

    buttons = [
        [
            InlineKeyboardButton(
                text="Aggiungere un evento",
                callback_data=str(ChatOrchestratorState.ADD_EVENT.value),
            ),
            InlineKeyboardButton(
                text="Cancellare un evento",
                callback_data=str(ChatOrchestratorState.DELETE_EVENT.value),
            ),
        ],
        [
            InlineKeyboardButton(
                text="Aggiorna le immagini degli eventi",
                callback_data=str(ChatOrchestratorState.MANAGE_EVENT_IMAGES.value),
            ),
        ],
        [
            InlineKeyboardButton(
                text="Creare una storia",
                callback_data=str(ChatOrchestratorState.CREATE_STORY.value),
            ),
            InlineKeyboardButton(
                text="Creare un post",
                callback_data=str(ChatOrchestratorState.CREATE_POST.value),
            ),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    await update.message.reply_text(
        "Ciao! Sono LudusSMA!\n"
        "Sono un assistente che ti aiuterà a gestire i tuoi social network!\n"
        "Utilizza il comando /help per sapere come posso aiutarti e scoprire tutte le mie funzionalità!\n"
        "Cosa vuoi fare?",
        reply_markup=keyboard,
    )

    return ChatOrchestratorState.SELECTING_ACTION


async def help(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "Al momento non sono in grado di fare molto... ma imparo in fretta e sto migliorando giorno dopo giorno!\n"
        "Ecco i comandi che al momento sono disponibili e cosa posso fare:\n"
        "  - /start: il comando con cui mi presento.\n"
        "  - /event: ti guido nella creazione di un evento, sulla base di questo verranno create delle storie su Instagram."
    )
    return ConversationHandler.END


async def add_event(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):

    event_types = [
        elem.strip("/").split("/")[-1].title()
        for elem in list_s3_folders(S3_BUCKET_IMAGES_NAME, "clean-images/")
    ] + ["Altro"]

    inline_keyboard_buttons = [
        InlineKeyboardButton(text=even_type, callback_data=even_type)
        for even_type in event_types
    ]

    buttons = [
        inline_keyboard_buttons[i : i + 2]
        for i in range(0, len(inline_keyboard_buttons), 2)
    ]

    markup = InlineKeyboardMarkup(buttons)
    message = "Ottimo! che tipo di evento vuoi creare?"

    if update.message:
        await update.message.reply_text(
            text=message,
            reply_markup=markup,
        )
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=markup,
        )

    return ChatOrchestratorState.ADD_EVENT


async def delete_event(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):

    message = "Questo comando non è ancora stato implementato."
    if update.message:
        await update.message.reply_text(text=message)
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=[[]],
        )
    return ConversationHandler.END


async def manage_event_images(
    update: telegram.Update, context: ContextTypes.DEFAULT_TYPE
):

    message = "Questo comando non è ancora stato implementato."
    if update.message:
        await update.message.reply_text(text=message)
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=[[]],
        )
    return ConversationHandler.END


async def create_story(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):

    message = "Questo comando non è ancora stato implementato."
    if update.message:
        await update.message.reply_text(text=message)
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=[[]],
        )
    return ConversationHandler.END


async def create_post(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):

    message = "Questo comando non è ancora stato implementato."
    if update.message:
        await update.message.reply_text(text=message)
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=[[]],
        )
    return ConversationHandler.END


async def help(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "Ecco i comandi che al momento sono disponibili e cosa posso fare:\n"
        "  - /start: il comando con cui mi presento e ti fornisco la lista delle funzionalità.\n"
        "  - /add_event: ti guido nella creazione di un evento, sulla base di questo verranno create delle storie su Instagram."
        "  - /done: Per resettare il processo e iniziare da capo.\n"
    )
    return ConversationHandler.END


async def done(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "Ciao! A presto!", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END