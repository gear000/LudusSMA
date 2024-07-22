import logging
from typing import Dict

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from dotenv import load_dotenv
from src.ludus_sma import LudusSMA
import os


# Enable logging
logger = logging.getLogger("SMA Logger")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
logger.addHandler(logging.StreamHandler())
logger.handlers[0].setFormatter(formatter)
logger.info("Starting SMA Bot")


load_dotenv()


CHOOSING, SUMMARY, CONFIRMATION, CONCLUSION = range(4)
CONTENT_TYPE = "Tipologia di contenuto"
TOPIC = "Argomento"


def check_identity(user_id: str) -> bool:
    """Check if the user is authorized to use bot"""
    authorized_users = os.getenv("AUTHORIZED_USERS").split(",")
    return user_id in authorized_users


def facts_to_str(user_data: Dict[str, str]) -> str:
    """Helper function for formatting the gathered user info."""
    facts = [f"{key} - {value}" for key, value in user_data.items()]
    return "\n".join(facts).join(["\n", "\n"])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask user for input."""

    reply_keyboard = [
        ["Descrizione", "Immagine"],
    ]
    markup = ReplyKeyboardMarkup(reply_keyboard)

    await update.message.reply_text(
        "Ciao! Sono LudusSMA, il Social Media Assistant di Ludus!\n"
        "Sono qui per aiutarti a generare delle descrizioni per i contenuti di Instagram. "
        "Cosa vorresti fare oggi?",
        reply_markup=markup,
    )

    return CHOOSING


async def choose_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask user for input."""

    reply_keyboard = [
        ["Post", "Storia"],
    ]
    markup = ReplyKeyboardMarkup(reply_keyboard)

    await update.message.reply_text(
        "Per quale tipo di contenuto vuoi generare una descrizione?",
        reply_markup=markup,
    )

    return CHOOSING


async def topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Ask the user for info about the topic of the description.
    """
    text = update.message.text
    if text != "No, aspetta...":
        context.user_data[CONTENT_TYPE] = text
    await update.message.reply_text(
        f"Su cosa vuoi generare la descrizione?",
        reply_markup=ReplyKeyboardRemove(),
    )

    return SUMMARY


async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store info provided by user and ask for confirmation."""
    text = update.message.text
    context.user_data[TOPIC] = text
    user_data = context.user_data

    reply_keyboard = [
        ["Vai!", "No, aspetta..."],
    ]
    markup = ReplyKeyboardMarkup(reply_keyboard)

    await update.message.reply_text(
        "Perfetto! Quindi ricapitolando:" f"{facts_to_str(user_data)}Proseguiamo?",
        reply_markup=markup,
    )

    return CONFIRMATION


async def get_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Generate description based on user input."""
    user_data = context.user_data
    content_type = user_data[CONTENT_TYPE]

    text = {
        "Post": "la descrizione per un post",
        "Storia": "la descrizione per una storia",
        "Immagine": "l'immagine",
    }.get(content_type)

    reply_keyboard = [
        ["Perfetta!", "Riproviamo..."],
    ]
    markup = ReplyKeyboardMarkup(reply_keyboard)

    await update.message.reply_text(
        f"Grande! Sto generando {text}...",
        reply_markup=ReplyKeyboardRemove(),
    )
    bot = LudusSMA()
    if content_type in ["Post", "Storia"]:
        descr = bot.get_description(
            content_type=user_data[CONTENT_TYPE], context=user_data[TOPIC]
        )
        await update.message.reply_text(descr["description"])
    else:
        img_url = bot.get_dalle_image(context=user_data[TOPIC])
        await update.message.reply_text(img_url["dalle_image_url"])
    await update.message.reply_text(
        "Che dici?",
        reply_markup=markup,
    )

    return CONCLUSION


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End the conversation."""

    await update.message.reply_text(
        f"Lieto di esserti stato utile!",
        reply_markup=ReplyKeyboardRemove(),
    )

    context.user_data.clear()
    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    import os

    # Create the Application and pass it your bot's token.
    TOKEN = os.getenv("telegram_token")
    if TOKEN is None:
        raise Exception("Telegram token not found")

    application = Application.builder().token(TOKEN).build()

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and SUMMARY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [
                MessageHandler(
                    filters.Regex("^(Post|Storia)$"),
                    topic,
                ),
                MessageHandler(
                    filters.Regex("^Descrizione$"),
                    choose_content,
                ),
                MessageHandler(
                    filters.Regex("^Immagine$"),
                    topic,
                ),
            ],
            SUMMARY: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex("^Done$")),
                    summary,
                )
            ],
            CONFIRMATION: [
                MessageHandler(
                    filters.Regex("^Vai!$"),
                    get_content,
                ),
                MessageHandler(
                    filters.Regex("^No, aspetta...$"),
                    topic,
                ),
            ],
            CONCLUSION: [
                MessageHandler(
                    filters.Regex("^Perfetta!$"),
                    done,
                ),
                MessageHandler(
                    filters.Regex("^Riproviamo...$"),
                    topic,
                ),
            ],
        },
        fallbacks=[
            MessageHandler(filters.Regex("^Done$"), done),
            CommandHandler("done", done),
        ],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
