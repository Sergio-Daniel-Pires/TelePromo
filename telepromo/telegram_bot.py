import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# First Level
SELECTING_ACTION = map(chr, range(1))

STOPPING, SHOWING = map(chr, range(8, 10))

END = ConversationHandler.END

(
    START,
    DONATION,
    SHOW_DONATE,
) = map(chr, range(10, 13))

# Top Level
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Select an action: Donation, Finalize, List wishs, New Wish"""
    text = (
        "Escolha uma dos botões abaixo:\n"
        "ou\n"
        "Para abrir menu ajuda: /help\n"
    )

    buttons = [
        [InlineKeyboardButton(text="Donation", callback_data=str(DONATION))],
        [InlineKeyboardButton(text="Novo produto", callback_data=str(DONATION))],
        [InlineKeyboardButton(text="Lista de Desejos", callback_data=str(DONATION))],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    if context.user_data.get(START):
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    else:
        await update.message.reply_text(
            "Olá, eu sou o Bot TelePromoBr, estou aqui para te ajudar a acompanhar preços/promoções de produtos"
        )
        await update.message.reply_text(text=text, reply_markup=keyboard)

    context.user_data[START] = False
    return SELECTING_ACTION

async def donation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """View the donations method and return"""
    donation_text = ("O criador desse bot é o Sérgio Pires @github\n"
                     "Caso queira me pagar uma breja, pode mandar neses PIX:\n" 
                     "**MEUPIX**"
                    )
    button = InlineKeyboardButton(text="Inicio", callback_data=str(END))
    keyboard = InlineKeyboardMarkup.from_button(button)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=donation_text, reply_markup=keyboard)

    context.user_data[START] = True
    
    return SHOW_DONATE

async def end_donation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    await start(update, context)

    return END

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End Conversation by command."""
    await update.message.reply_text("Okay, bye.")
    return END

async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End conversation from InlineKeyboardButton."""
    await update.callback_query.answer()

    text = "See you around!"
    await update.callback_query.edit_message_text(text=text)
    return END

#class TelegramBot():
#    def __init__(self, database) -> None:
#        database = database

# Pague uma breja
def main():
    application = Application.builder().token("6163736593:AAFRImnBRLZ3Ra7TRuECvoBT1juJQmNxUv8").build()

    donation_conv = ConversationHandler(
        entry_points={
            CallbackQueryHandler(end_donation, pattern="^" + str(END) + "$"),
        },
        states={},
        fallbacks=[
            CommandHandler("stop", stop),
        ],
        map_to_parent={
            END: SELECTING_ACTION,
        },
    )

    selection_handlers = [
        CallbackQueryHandler(donation, pattern="^" + str(DONATION) + "$")
    ]
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SHOWING: [CallbackQueryHandler(start, pattern="^" + str(END) + "$")],
            SHOW_DONATE: [donation_conv],
            SELECTING_ACTION: selection_handlers,
            STOPPING: [CommandHandler("start", start)]
        },
        fallbacks=[
            CommandHandler("stop", stop)
        ]
    )

    application.add_handler(handler=conv_handler)

    application.run_polling()

if __name__ == "__main__":
    main()