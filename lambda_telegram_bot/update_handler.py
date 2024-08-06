"""In this file we will create the update handler for the bot."""

from datetime import date
from enum import Enum
import os
from typing import Dict
import telegram
import logging
from telegram.ext import ContextTypes, ConversationHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.constants import ParseMode

from utils.aws_utils import list_s3_folders, create_scheduler
from .chatbot.event_handler import check_info_chain, OutputCreateEvent, Event

### Setup Logging ###
logger = logging.getLogger("Update Handeler")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
logger.addHandler(logging.StreamHandler())
logger.handlers[0].setFormatter(formatter)

### Environment Variables ###
S3_BUCKET_IMAGES_NAME = os.getenv("S3_BUCKET_IMAGES_NAME", "ludussma-images")
DYNAMODB_TABLE_CHATS_HISTORY_NAME = os.getenv(
    "DYNAMODB_TABLE_CHATS_HISTORY_NAME", "ChatsHistory"
)

EVENT_TYPE = "Tipo di evento"
CONTEXT = "Informazioni sull'evento"

EVENT_KEYS = {
    "title": "Titolo",
    "description": "Descrizione",
    "start_date": "Data di inizio",
    "end_date": "Data di fine",
    "start_time": "Ora di inizio",
    "end_time": "Ora di fine",
    "location": "Luogo",
    "other_info": "Altre informazioni",
}


class ChatState(Enum):
    INTRO = 0
    ADD_EVENT = 1
    EVENT_TYPE = 2
    EVENT_INFO = 3
    LLM_PROCESSING = 4
    RECAP = 5
    CREATE_EVENT = 6
    CONCLUSION = 7


def facts_to_str(event_data: Event) -> str:
    """Helper function for formatting the gathered user info."""

    event_data: dict = event_data.model_dump()

    event_data["start_time"] = event_data["start_date"].time()
    event_data["start_date"] = event_data["start_date"].date()

    event_data["end_time"] = event_data["end_date"].time()
    event_data["end_date"] = event_data["end_date"].date()

    # event_data.start_time = event_data.start_date.split("T")[1]
    # event_data.start_date = event_data.start_date.split("T")[0]

    # event_data.end_time = event_data.end_date.split("T")[1]
    # event_data.end_date = event_data.end_date.split("T")[0]

    facts = [f"<b>{EVENT_KEYS[key]}</b>: {event_data[key]}" for key in EVENT_KEYS]
    return "\n\n - " + "\n - ".join(facts)


# region Commands
async def start(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the conversation and ask user for input."""

    await update.message.reply_text(
        "Ciao! Sono LudusSMA!\n"
        "Sono un assistente che ti aiuterà a gestire i tuoi social network!\n"
        "Utilizza il comando /help per sapere come posso aiutarti e scoprire tutte le mie funzionalità!"
    )

    markup = ReplyKeyboardMarkup([["Aggiungere un evento", "Caricare un'immagine"]])
    await update.message.reply_text(
        "Cosa vuoi fare oggi?",
        reply_markup=markup,
    )

    return ChatState.INTRO


async def help(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "Al momento non sono in grado di fare molto... ma imparo in fretta e sto migliorando giorno dopo giorno!\n"
        "Ecco i comandi che al momento sono disponibili e cosa posso fare:\n"
        "  - /start: il comando con cui mi presento.\n"
        "  - /event: ti guido nella creazione di un evento, sulla base di questo verranno create delle storie su Instagram."
    )


async def choose_event_type(
    update: telegram.Update, context: ContextTypes.DEFAULT_TYPE
):

    event_types = [
        elem.strip("/").split("/")[-1].title()
        for elem in list_s3_folders(S3_BUCKET_IMAGES_NAME, "clean-images/")
    ] + ["Altro"]

    markup = ReplyKeyboardMarkup([event_types])

    await update.message.reply_text(
        "Ottimo! che tipo di evento vuoi creare?",
        reply_markup=markup,
    )

    return ChatState.ADD_EVENT


async def event(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    if not context.user_data.get(EVENT_TYPE):
        context.user_data[EVENT_TYPE] = text

        await update.message.reply_text(
            "Perfetto! 😊\n"
            "Per creare un evento ho bisogno di queste info:\n"
            "  - il nome dell'evento;\n"
            "  - una descrizione dell'evento;\n"
            "  - quando sarà l'evento, cioè, data e ora di inizio e data e ora di fine;\n"
            "  - dove si terrà l'evento, cioè il nome del posto o l'indirizzo.",
            reply_markup=ReplyKeyboardRemove(),
        )
    else:
        await update.message.reply_text(
            "Va bene, che informazione vuoi darmi?",
            reply_markup=ReplyKeyboardRemove(),
        )

    return ChatState.EVENT_INFO


async def llm_processing(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Instantiate the bot and get the answer
    """
    text = update.message.text

    if context.user_data.get(CONTEXT):
        context.user_data[CONTEXT] += "\nAlice: " + text
    else:
        context.user_data[CONTEXT] = "Alice: " + text

    response: OutputCreateEvent = check_info_chain.invoke(
        {"input": context.user_data[CONTEXT], "today": date.today()}
    )
    clarification = response.clarification
    if clarification:
        await update.message.reply_text(
            "Mmhh, qualcosa non va...\n" + clarification,
            reply_markup=ReplyKeyboardRemove(),
        )
        context.user_data[CONTEXT] += "\nBob: " + clarification
    else:

        await update.message.reply_text(
            "Bene, allora creo un evento con queste informazioni:"
            + facts_to_str(response.event),
            parse_mode=ParseMode.HTML,
        )
        markup = ReplyKeyboardMarkup([["Vai con l'evento!", "No, aspetta..."]])
        await update.message.reply_text("Cosa facciamo?", reply_markup=markup)

        return ChatState.RECAP


async def add_image_first(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    """Add an image in the container"""
    await update.message.reply_text(
        "Aggiungi l'immagine per lo sfondo prima 🙃",
        reply_markup=ReplyKeyboardRemove(),
    )
    await update.message.reply_text(
        f"Lieto di esserti stato utile!",
    )

    context.user_data.clear()
    return ConversationHandler.END


async def schedule_event(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    """Add event in scheduler"""

    # TODO
    # add logic
    # create_scheduler()

    await update.message.reply_text(
        f"Questa è la logica mokkata di aggiunta di un evento",
        reply_markup=ReplyKeyboardRemove(),
    )
    await update.message.reply_text(
        f"Ho creato l'evento!",
    )
    await update.message.reply_text(
        f"Lieto di esserti stato utile!",
    )

    context.user_data.clear()
    return ConversationHandler.END


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End the conversation."""

    await update.message.reply_text(
        f"Lieto di esserti stato utile!",
        reply_markup=ReplyKeyboardRemove(),
    )

    context.user_data.clear()
    return ConversationHandler.END


# endregion


# region TODO
async def audio_handler(
    update: telegram.Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Handle audio messages
    """
    await update.message.reply_text(
        "Purtroppo non sono ancora in grado di ascoltare i tuoi messaggi audio ☹️",
        reply_markup=ReplyKeyboardRemove(),
    )

    context.user_data.clear()
    return ConversationHandler.END


async def media_handler(
    update: telegram.Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Handle audio messages
    """
    await update.message.reply_text(
        "Purtroppo non sono ancora in grado di vedere le tue foto e i tuoi video ☹️",
        reply_markup=ReplyKeyboardRemove(),
    )

    context.user_data.clear()
    return ConversationHandler.END


# endregion
