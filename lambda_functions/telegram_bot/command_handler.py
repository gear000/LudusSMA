import telegram

from telegram.ext import ContextTypes


async def start(update: telegram.Update, context):
    """Start the conversation and ask user for input."""

    reply_keyboard = [
        ["Crea Evento", "Descrizione"],
    ]
    markup = telegram.ReplyKeyboardMarkup(reply_keyboard)

    reply_anwser = await update.message.reply_text(
        "Ciao! Sono LudusSMA, il Social Media Assistant di Ludus!\n"
        "Sono qui per aiutarti a creare eventi e generare delle descrizioni per i contenuti di Instagram. "
        "Cosa vorresti fare oggi?",
        reply_markup=markup,
    )

    print(f"Reply Awnser:\n {reply_anwser}")


async def event(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask user for input."""

    reply_anwser = await update.message.reply_text("Elaboro l'evento")

    print(f"Reply Awnser:\n {reply_anwser}")

    return 0
