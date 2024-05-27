import telegram
import logging
from telegram.ext import ContextTypes

from chatbot.event_handler import EventHandler

### Setup Logging ###
logger = logging.getLogger("Update Handeler")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
logger.addHandler(logging.StreamHandler())
logger.handlers[0].setFormatter(formatter)

### Handlers ###


async def start(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask user for input."""

    await update.message.reply_text(
        "Ciao! Sono LudusSMA!\n"
        "Sono un assistente che ti aiuterà a gestire i tuoi social network!\n"
        "Utilizza il comando /help per sapere come posso aiutarti e scoprire tutte le mie funzionalità!"
    )


async def help(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Al momento sono in grado di fare molto, ma imparo in fretta e sto migliorando giorno dopo giorno!\n"
        "Ecco i comandi che al momento sono disponibili e cosa posso fare:\n"
        "  - /start: il comando con cui mi presento.\n"
        "  - /event: ti guido nella creazione di un evento, sulla base di questo verranno create delle storie su Instagram."
    )


async def event(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Grande! Creiamo un evento!\n"
        "Per creare un evento ho bisogno di:\n"
        "  - il nome dell'evento;\n"
        "  - la descrizione dell'evento;\n"
        "  - quando sarà l'evento, cioè il giorno (o i giorni) e quando inizia e finisce;\n"
        "  - dove si terrà l'evento, cioè l'indirizzo e la città (se necessario includi anche il nome del posto, es. Kubo).\n"
        "Quale evento creiamo oggi?"
    )


async def my_event_handler(
    update: telegram.Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Instantiate the bot and get the answer
    """
    # TODO
    # get chat_history from DB
    # context._user_id
    # context._chat_id
    # chat_history = get_history(user_id, chat_id)
    bot = EventHandler(chat_history=[])
    answer_dict = bot.run(update.message.text)
    reply_anwser = await update.message.reply_text(answer_dict["output"])

    print(f"Reply Answer:\n {reply_anwser}")

    return 0
