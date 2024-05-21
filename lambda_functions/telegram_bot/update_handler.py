import telegram
from telegram.ext import ContextTypes

from chatbot.event_handler import EventHandler


async def start(update: telegram.Update, context):
    """Start the conversation and ask user for input."""

    # reply_keyboard = [
    #     ["Crea Evento", "Descrizione"],
    # ]
    # markup = telegram.ReplyKeyboardMarkup(reply_keyboard)

    reply_anwser = await update.message.reply_text(
        "Ciao! Sono Giulio!\n"
        "Sono qui per aiutarti a creare eventi.\n"
        "Per creare un evento ho bisogno di:\n"
        "   - il nome dell'evento;\n"
        "   - la descrizione dell'evento;\n"
        "   - quando sarà l'evento, cioè il giorno (o i giorni) e quando inizia e finisce;\n"
        "   - dove si terrà l'evento, cioè l'indirizzo e la città (se necessario includi ache il nome del posto, es. Kubo).\n"
        "Quale evento creiamo oggi?",
        # reply_markup=markup,
    )

    print(f"Reply Answer:\n {reply_anwser}")


async def event(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
