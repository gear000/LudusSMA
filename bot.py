import logging
import os
from dotenv import load_dotenv

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

from src.ludus_sma import LudusSMA

logger = logging.getLogger("SMA Logger")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
logger.addHandler(logging.StreamHandler())
logger.handlers[0].setFormatter(formatter)
logger.info("Starting SMA Bot")

load_dotenv()

DESCRIPTION, IMAGE, CONTEXT, CONTENT_TYPE = range(4)


# ---------- SMA interaction
async def get_content_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ludus_sma_bot = LudusSMA()
    ctx = update.message.text
    await update.message.reply_text("Descrizione")  # ludus_sma_bot.get_description())
    # await context.bot.send_message(
    #     chat_id=update.effective_chat.id, text="Ciao! Sono il tuo bot."
    # )


# ---------- Utils


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # text = "Puoi scegliere se generare una descrizione per un contenuto oppure generare un immagine."

    # buttons = [
    #     [
    #         InlineKeyboardButton(
    #             text="Genera una descrizione", callback_data=str(DESCRIPTION)
    #         ),
    #         InlineKeyboardButton(text="Genera un'immagine", callback_data=str(IMAGE)),
    #     ],
    # ]

    # keyboard = InlineKeyboardMarkup(buttons)

    text = "Per ora puoi generare una descrizione per un contenuto."
    await update.message.reply_text("Ciao! Sono il tuo bot.")
    await update.message.reply_text(text=text)  # , reply_markup=keyboard)

    return CONTENT_TYPE


async def content_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [["Post", "Storia"]]
    await update.message.reply_text(
        "Per che tipo di contenuto vuoi generare la descrizione? Un post o una storia?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Post o storia?",
        ),
    )
    return CONTEXT


async def context(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data[CONTENT_TYPE] = update.callback_query.data
    text = "Ottimo! Quale dovrebbe essere il contenuto della descrizione?"

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    await update.message.reply_text(
        "Bye! I hope we can talk again some day."  # , reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main():
    TOKEN = os.getenv("telegram_token")
    if TOKEN is None:
        raise Exception("Telegram token not found")

    application = Application.builder().token(TOKEN).build()

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CONTENT_TYPE: [
                MessageHandler(filters.Regex("^(Post|Storia)$"), content_type)
            ],
            CONTEXT: [MessageHandler(filters.TEXT, context)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
