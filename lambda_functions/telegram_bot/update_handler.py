import os
import telegram
import logging
from telegram.ext import ContextTypes

from utils.aws_utils import (
    get_record_from_dynamo,
    insert_record_in_dynamo,
    clear_history,
)
from chatbot.event_handler import EventHandler

from datetime import datetime

### Setup Logging ###
logger = logging.getLogger("Update Handeler")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
logger.addHandler(logging.StreamHandler())
logger.handlers[0].setFormatter(formatter)

### Environment Variables ###
DYNAMODB_TABLE_CHATS_HISTORY_NAME = os.environ["DYNAMODB_TABLE_CHATS_HISTORY_NAME"]


### Handlers ###


async def start(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask user for input."""
    user_id = update.effective_user.id
    clear_history(table_name=DYNAMODB_TABLE_CHATS_HISTORY_NAME, user_id=str(user_id))

    await update.message.reply_text(
        "Ciao! Sono LudusSMA!\n"
        "Sono un assistente che ti aiuterà a gestire i tuoi social network!\n"
        "Utilizza il comando /help per sapere come posso aiutarti e scoprire tutte le mie funzionalità!"
    )


async def help(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    clear_history(table_name=DYNAMODB_TABLE_CHATS_HISTORY_NAME, user_id=str(user_id))

    await update.message.reply_text(
        "Al momento sono in grado di fare molto, ma imparo in fretta e sto migliorando giorno dopo giorno!\n"
        "Ecco i comandi che al momento sono disponibili e cosa posso fare:\n"
        "  - /start: il comando con cui mi presento.\n"
        "  - /event: ti guido nella creazione di un evento, sulla base di questo verranno create delle storie su Instagram."
    )


async def event(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    clear_history(table_name=DYNAMODB_TABLE_CHATS_HISTORY_NAME, user_id=str(user_id))

    await update.message.reply_text(
        "Grande! Creiamo un evento!\n"
        "Per creare un evento ho bisogno di:\n"
        "  - il nome dell'evento;\n"
        "  - la descrizione dell'evento;\n"
        "  - quando sarà l'evento, cioè il giorno (o i giorni) e quando inizia e finisce;\n"
        "  - dove si terrà l'evento, cioè il nome del posto o l'indirizzo.\n"
        "Quale evento creiamo oggi?"
    )


async def my_event_handler(
    update: telegram.Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Instantiate the bot and get the answer
    """
    user_id = update.effective_user.id
    st = str(datetime.now())

    bot = EventHandler()

    try:
        answer_dict = bot.run(update.message.text, user_id=str(user_id))

        reply_answer = await update.message.reply_text(answer_dict["output"])
        print(f"Reply Answer:\n {reply_answer}")
    except Exception as e:
        logger.error(e)
        reply_answer = await update.message.reply_text(
            f"Si è verificato un errore: {e}"
        )

    return 0
