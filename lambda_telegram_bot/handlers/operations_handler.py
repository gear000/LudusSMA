from datetime import date
from enum import Enum
import os
import re
import telegram

from telegram.constants import ParseMode

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from utils.aws_utils import (
    delete_s3_object,
    delete_schedule_group,
    get_s3_object,
    list_s3_objects,
    move_s3_object,
    put_s3_object,
    transcribe_audio,
)
from utils.formatter_utils import format_event_types
from utils.telegram_utils import send_event_types
from utils.logger_utils import *
from utils.models.model_utils import Event, OutputCreateEvent

from chatbot import tools
from chatbot.event_handler import check_info_chain

from .chat_state import (
    ChatManageEventTypeState,
    ChatOrchestratorState,
    ChatAddEventState,
)
from .commands_handler import *

__all__ = [
    "selecting_action_handler",
    "add_event_handler",
    "delete_event_handler",
    "manage_event_type_handler",
    "create_story_handler",
    "create_post_handler",
    "error_handler",
]

S3_BUCKET_IMAGES_NAME = os.environ["S3_BUCKET_IMAGES_NAME"]
S3_BUCKET_CHAT_PERSISTENCE_NAME = os.environ["S3_BUCKET_CHAT_PERSISTENCE_NAME"]


class ContextKeys(Enum):
    """
    These instances are used in the Telegram chat context dictionary as keys.
    In this way is possible to have a description as metadata for each key.
    """

    EVENT_TYPE = "Tipo di evento"
    EVENT = "Informazioni sull'evento"
    CONTEXT = "Messaggi dell'utente"
    START_OVER = "Start Over"
    EVENT_TYPE_DICT = "Dizionario degli eventi disponibili"
    NEW_EVENT = "Titolo del nuovo evento"


async def selecting_action_handler(
    update: telegram.Update, context: ContextTypes.DEFAULT_TYPE
):
    """
    This step acts as a router on the user's initial choice if the `/start` commad is used.
    """
    state = int(update.callback_query.data)
    match ChatOrchestratorState(state):
        case ChatOrchestratorState.ADD_EVENT:
            return await add_event(update, context)
        case ChatOrchestratorState.DELETE_EVENT:
            return await delete_event(update, context)
        case ChatOrchestratorState.MANAGE_EVENT_TYPE:
            return await manage_event_type(update, context)
        case ChatOrchestratorState.CREATE_STORY:
            return await create_story(update, context)
        case ChatOrchestratorState.CREATE_POST:
            return await create_post(update, context)

    raise ValueError("State not found")


async def error_handler(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Log the mishandling of an update either in CloudWatch logs or as a message on Telegram
    """
    logger.error(
        "Update '%s' caused error '%s'",
        update,
        context.error,
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="C'è stato un errore nell'elaborazione del messaggio.\nAspetta 30 secondi poi prova a resettare il bot con il comando /done o contatta un amministratore se l'errore persiste.",
    )

    raise context.error


async def not_implemented(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    """
    This step indicates to the user that a function or command has not yet been implemented.
    """
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Questa funzione non è ancora implementata.",
    )


# region Add Event


async def set_event(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    """
    In this step you ask for information about the individual event that the user intends to create.
    Or if the user intends to correct the description they gave earlier.
    """

    # if ContextKeys.EVENT_TYPE is empty, it means that this is the first user interaction for
    # this specific event, so it is necessary to make a detailed list of the required fields
    if not context.user_data.get(ContextKeys.EVENT_TYPE):
        text = update.callback_query.data
        context.user_data[ContextKeys.EVENT_TYPE] = text
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "Perfetto! 😊\n"
            "Per creare un evento ho bisogno di queste info:\n"
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


async def llm_processing(
    update: telegram.Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_message: str | None = None,
):
    """
    This step is used to process the event description through LLM, checking the completeness of the information and creating the appropriate `Event` instance.
    If any data is missing, the process will ask the user for the opposite information.

    :param update: telegram.Update, the user update from Telegram
    :param context: ContextTypes.DEFAULT_TYPE, the context of the conversation
    :param user_message: str | None, if the update contained an audio `user_message` contains the transcribed message text
    """
    text = update.message.text or user_message

    if context.user_data.get(ContextKeys.CONTEXT):
        context.user_data[ContextKeys.CONTEXT].append(("user", text))
    else:
        context.user_data[ContextKeys.CONTEXT] = [("user", text)]

    response: OutputCreateEvent = check_info_chain.invoke(
        {
            "input": context.user_data[ContextKeys.CONTEXT],
            "today": date.today(),
            "event_type": context.user_data[ContextKeys.EVENT_TYPE],
        }
    )
    clarification = response.clarification

    if clarification:
        await update.message.reply_text(
            "Mmhh, qualcosa non va...\n" + clarification,
            reply_markup=ReplyKeyboardRemove(),
        )
        context.user_data[ContextKeys.CONTEXT].append(("assistant", clarification))
        return ChatAddEventState.EVENT_INFO
    else:
        event: Event = response.event
        event.event_type = context.user_data[ContextKeys.EVENT_TYPE]
        await update.message.reply_text(
            "Bene, allora queste sono le informazioni che ho recuperato:"
            + event.format_for_tg_message(),
            parse_mode=ParseMode.HTML,
        )
        context.user_data[ContextKeys.EVENT] = event
        markup = ReplyKeyboardMarkup(
            [["Vai con l'evento!", "No, aspetta..."]], one_time_keyboard=True
        )
        await update.message.reply_text("Cosa facciamo?", reply_markup=markup)

        return ChatAddEventState.RECAP


async def llm_processing_audio(
    update: telegram.Update, context: ContextTypes.DEFAULT_TYPE
):
    """
    This step is used to transcribe the audio file to text for Event description
    """
    audio_file = await update.message.voice.get_file()
    audio_s3_key = f"{update.effective_chat.id}/audio/{audio_file.file_id}.mp3"

    put_s3_object(
        bucket_name=S3_BUCKET_CHAT_PERSISTENCE_NAME,
        object_key=audio_s3_key,
        body=await audio_file.download_as_bytearray(),
    )

    transcribe_text = transcribe_audio(
        audio_key=f"s3://{S3_BUCKET_CHAT_PERSISTENCE_NAME}/{audio_s3_key}"
    )

    return await llm_processing(
        update=update, context=context, user_message=transcribe_text
    )


async def schedule_event(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Create several schedulers for the single event, for create scheduled Instagram stories.
    """

    tools.create_schedules(context.user_data[ContextKeys.EVENT])

    await update.message.reply_text(
        f"Ho creato l'evento!",
    )

    return await done(update, context)


add_event_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(callback=set_event),
    ],
    name="add_event",
    persistent=True,
    allow_reentry=True,
    states={
        ChatAddEventState.EVENT_INFO: [
            MessageHandler(filters.TEXT & ~(filters.COMMAND), llm_processing),
            MessageHandler(filters=filters.VOICE, callback=llm_processing_audio),
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
    fallbacks=[],
)

# endregion

# region Delete Event


async def deleting_event(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Delete schedule group that a specif single event belongs to.
    """

    logger.info("Deleting event %s", update.callback_query.data)
    delete_schedule_group(update.callback_query.data)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "Ho cancellato l'evento!",
    )

    return await done(update, context)


delete_event_handler = CallbackQueryHandler(callback=deleting_event, pattern="^.*$")

# endregion

# region Manage Event Images


async def create_new_event_type(
    update: telegram.Update, context: ContextTypes.DEFAULT_TYPE
):
    """
    Requires the name for the construction of the new event type.
    """
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "Sono contento ci sia un nuovo evento a Ludus!\n"
        "Sotto che tipologia inseriamo l'evento? Ricorda che il titolo dovrebbe essere unico e molto coinciso.\n"
        "Inoltre, ogni spazio sarà sostituito da un trattino ed ogni carattere speciale rimosso.",
        reply_markup=InlineKeyboardMarkup([[]]),
    )

    return ChatManageEventTypeState.SET_NEW_EVENT_TYPE


async def request_image(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    """
    It handles conflicts of event types that possess the same identifier and in case of successful
    processing requests the image to be associated with the event type.
    """

    event_types = format_event_types()

    event_type = re.sub(r"[^a-zA-Z0-9 -]", "", update.message.text.strip())
    event_type = event_type.replace(" ", "-").lower()

    if event_type in event_types:
        await update.message.reply_text(
            "Purtroppo un altro evento ha lo stesso nome. Magari potremmo scegliere un altro titolo."
        )
        return ChatManageEventTypeState.SET_NEW_EVENT_TYPE
    else:
        context.user_data[ContextKeys.NEW_EVENT] = event_type
        await update.message.reply_text(
            "Perfetto! Ora abbiamo bisogno di un immagine per le storie.\n"
            "Ricorda che l'immagine dovrebbe avere dimensioni 1080 px per 1920 px (con proporzioni di 9:16)."
        )

    return ChatManageEventTypeState.LOAD_IMAGE


async def load_image(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Upload the image to S3, this consequently creates a new event type.
    """
    photo_file = await update.message.photo[-1].get_file()

    put_s3_object(
        bucket_name=S3_BUCKET_IMAGES_NAME,
        object_key=f"clean-images/{context.user_data[ContextKeys.NEW_EVENT]}/{photo_file.file_id}.jpg",
        body=await photo_file.download_as_bytearray(),
    )
    await update.message.reply_text(
        "Il nuovo tipo evento è stato creato! Prova subito a creare un nuovo evento con /add_event !"
    )

    return ConversationHandler.END


async def update_event_type(
    update: telegram.Update, context: ContextTypes.DEFAULT_TYPE
):
    """
    Asks the user to choose the type of event to update from those available.
    """
    are_there_event_type = await send_event_types(
        update,
        context,
        "Che tipologia di evento vuoi AGGIORNARE?",
    )

    if are_there_event_type:
        return ChatManageEventTypeState.EXPOSE_UPDATING_ACTION

    return ConversationHandler.END


async def expose_updating_action(
    update: telegram.Update, context: ContextTypes.DEFAULT_TYPE
):
    """
    Once you have chosen the type of event to be updated you are asked which operation you want to perform between:
    - update the event type label
    - update the event type image
    - check the current image
    """
    context.user_data[ContextKeys.EVENT_TYPE] = update.callback_query.data.lower()

    buttons = [
        [
            InlineKeyboardButton(
                text="Aggiorna label del tipo di evento",
                callback_data="update_event_type_label",
            )
        ],
        [
            InlineKeyboardButton(
                text="Aggiorna immagine del tipo di evento",
                callback_data="update_event_type_image",
            )
        ],
        [
            InlineKeyboardButton(
                text="Verifica l'immagine attuale",
                callback_data="check_event_type_image",
            )
        ],
    ]

    markup = InlineKeyboardMarkup(buttons)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "Perfetto! Cosa vuoi fare?", reply_markup=markup
    )
    return ChatManageEventTypeState.SELECTING_UPDATING_ACTION


async def update_event_type_label(
    update: telegram.Update, context: ContextTypes.DEFAULT_TYPE
):
    """
    The new label for the event type is requested.
    """
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "Va bene! Quale nuova label vuoi dare a questo tipo di evento?"
        "Ricorda che il titolo dovrebbe essere unico e molto coinciso.\n"
        "Inoltre, ogni spazio sarà sostituito da un trattino ed ogni carattere speciale rimosso.",
        reply_markup=InlineKeyboardMarkup([[]]),
    )

    return ChatManageEventTypeState.UPDATE_LABEL


async def validate_label(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    """
    The new label is validated, verifying that there is not already another event with the same title. If so, the image is moved to a new S3 key.
    """

    event_types = format_event_types()

    event_type = re.sub(r"[^a-zA-Z0-9 -]", "", update.message.text.strip())
    event_type = event_type.replace(" ", "-").lower()

    if event_type in event_types:
        await update.message.reply_text(
            "Purtroppo un altro evento ha lo stesso nome. Magari potremmo scegliere un altro titolo."
        )
        return ChatManageEventTypeState.UPDATE_LABEL
    else:
        images_list = list_s3_objects(
            bucket_name=S3_BUCKET_IMAGES_NAME,
            prefix=f"clean-images/{context.user_data[ContextKeys.EVENT_TYPE]}/",
        )

        image_key = [
            image_key["Key"]
            for image_key in images_list
            if image_key["Key"].split(".")[-1] in ["jpg", "jpeg", "png"]
        ].pop()

        move_s3_object(
            bucket_name=S3_BUCKET_IMAGES_NAME,
            object_key=image_key,
            new_key=f"clean-images/{event_type}/{image_key.split('/')[-1]}",
        )

        await update.message.reply_text(
            f"Perfetto! La label è stata aggiornata da {context.user_data[ContextKeys.EVENT_TYPE]} a {event_type}."
        )

        return ConversationHandler.END


async def update_event_type_image(
    update: telegram.Update, context: ContextTypes.DEFAULT_TYPE
):
    """
    The new image for the event type is requested.
    """
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        f"Ottimo! Carica pure la nuova immagine per {context.user_data[ContextKeys.EVENT_TYPE].title()}.\n"
        "Ricorda che l'immagine dovrebbe avere dimensioni 1080 px per 1920 px (con proporzioni di 9:16).",
        reply_markup=InlineKeyboardMarkup([[]]),
    )

    return ChatManageEventTypeState.UPDATE_IMAGE


async def validate_image(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    """
    The old image is deleted and the new one is uploaded to S3
    """

    delete_s3_object(
        bucket_name=S3_BUCKET_IMAGES_NAME,
        object_key=f"clean-images/{context.user_data[ContextKeys.EVENT_TYPE]}/",
        recursive=True,
    )

    photo_file = await update.message.photo[-1].get_file()

    put_s3_object(
        bucket_name=S3_BUCKET_IMAGES_NAME,
        object_key=f"clean-images/{context.user_data[ContextKeys.EVENT_TYPE]}/{photo_file.file_id}.jpg",
        body=await photo_file.download_as_bytearray(),
    )

    await update.message.reply_text(
        f"Perfetto! La nuova immagine per {context.user_data[ContextKeys.EVENT_TYPE]} è stata caricata"
    )

    return ConversationHandler.END


async def check_event_type_image(
    update: telegram.Update, context: ContextTypes.DEFAULT_TYPE
):
    """
    Send the image related to the requested event type uploaded to S3 and used as the basis for creating the story on Instagram
    """
    event_type: str = context.user_data[ContextKeys.EVENT_TYPE]

    images_list = list_s3_objects(
        bucket_name=S3_BUCKET_IMAGES_NAME,
        prefix=f"clean-images/{event_type}/",
    )

    image_key = [
        image_key["Key"]
        for image_key in images_list
        if image_key["Key"].split(".")[-1] in ["jpg", "jpeg", "png"]
    ].pop()

    event_image = get_s3_object(
        bucket_name=S3_BUCKET_IMAGES_NAME,
        object_key=image_key,
    ).read()

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        f"Ecco l'immagine per il tipo di evento {event_type.title()}",
        reply_markup=InlineKeyboardMarkup([[]]),
    )

    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=event_image,
    )

    return ConversationHandler.END


async def delete_event_type(
    update: telegram.Update, context: ContextTypes.DEFAULT_TYPE
):
    """
    Lists the possible types of events that can be deleted by the user
    """
    is_any_event_type = await send_event_types(
        update,
        context,
        "Che tipologia di evento vuoi CANCELLARE?",
    )

    if is_any_event_type:
        return ChatManageEventTypeState.DELETING


async def deleting_event_type(
    update: telegram.Update, context: ContextTypes.DEFAULT_TYPE
):
    """
    Delete an event type as S3 key
    """
    delete_s3_object(
        bucket_name=S3_BUCKET_IMAGES_NAME,
        object_key=f"clean-images/{update.callback_query.data.lower()}",
        recursive=True,
    )
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        f"Il tipo di evento: {update.callback_query.data.title()} è stato cancellato!",
        reply_markup=InlineKeyboardMarkup([[]]),
    )

    return ConversationHandler.END


manage_event_type_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            callback=create_new_event_type, pattern="^add_event_type$"
        ),
        CallbackQueryHandler(callback=update_event_type, pattern="^update_event_type$"),
        CallbackQueryHandler(callback=delete_event_type, pattern="^delete_event_type$"),
    ],
    name="manage_event_type",
    persistent=True,
    allow_reentry=True,
    states={
        ChatManageEventTypeState.SET_NEW_EVENT_TYPE: [
            MessageHandler(filters.TEXT & ~(filters.COMMAND), request_image)
        ],
        ChatManageEventTypeState.LOAD_IMAGE: [
            MessageHandler(filters.PHOTO, load_image)
        ],
        ChatManageEventTypeState.EXPOSE_UPDATING_ACTION: [
            CallbackQueryHandler(callback=expose_updating_action)
        ],
        ChatManageEventTypeState.SELECTING_UPDATING_ACTION: [
            CallbackQueryHandler(
                callback=update_event_type_label, pattern="^update_event_type_label$"
            ),
            CallbackQueryHandler(
                callback=update_event_type_image, pattern="^update_event_type_image$"
            ),
            CallbackQueryHandler(
                callback=check_event_type_image, pattern="^check_event_type_image$"
            ),
        ],
        ChatManageEventTypeState.UPDATE_LABEL: [
            MessageHandler(filters.TEXT & ~(filters.COMMAND), validate_label)
        ],
        ChatManageEventTypeState.UPDATE_IMAGE: [
            MessageHandler(filters.PHOTO, validate_image)
        ],
        ChatManageEventTypeState.DELETING: [
            CallbackQueryHandler(callback=deleting_event_type)
        ],
    },
    fallbacks=[],
)

# endregion

# region Other Operations

create_story_handler = ConversationHandler(entry_points=[], states={}, fallbacks=[])
create_post_handler = ConversationHandler(entry_points=[], states={}, fallbacks=[])

# endregion
