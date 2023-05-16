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
SELECTING_ACTION, SELECTING_CATEGORY, ADDING = map(chr, range(3))

# Second
ELETRONICS, OTHERS = map(chr, range(4, 6))

# Third
ANOTHER_PRODUCT = map(chr, range(7, 9))

STOPPING, SHOWING, TYPING = map(chr, range(9, 12))

END = ConversationHandler.END

(
    START,
    DONATION,
    SHOW_DONATE,
    RETURN
) = map(chr, range(11, 15))

# Top Level
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Select an action: Donation, Finalize, List wishs, New Wish"""
    text = (
        "Escolha uma dos botões abaixo:\n"
        "ou\n"
        "Para abrir menu ajuda: /help\n"
    )

    buttons = [
        [InlineKeyboardButton(text="Fortalecer Breja", callback_data=str(DONATION))],
        [InlineKeyboardButton(text="Novo produto", callback_data=str(SELECTING_CATEGORY))],
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
    
    return SHOWING

async def select_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Add new product"""
    select_category_text = (
        "Selecione a categoria do produto:\n"
    )
    buttons = [
        [InlineKeyboardButton(text="Eletronicos", callback_data=str(ELETRONICS))],
        [InlineKeyboardButton(text="Outros", callback_data=str(OTHERS))],
        [InlineKeyboardButton(text="Inicio", callback_data=str(END))]
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=select_category_text, reply_markup=keyboard)

    return ADDING

async def ask_for_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    new_product_text = (
        "Escreva abaixo o nome do produto:\n"
    )
    button = InlineKeyboardButton(text="Voltar", callback_data=str(RETURN))
    keyboard = InlineKeyboardMarkup.from_button(button)
    await update.callback_query.edit_message_text(text=new_product_text, reply_markup=keyboard)

    context.user_data[START] = True

    return TYPING

async def save_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    #
    # Salvar produto no Mongo
    #
    ask_new_product = (
            "Adicionado! Deseja adicionais mais?"
        )
    
    buttons = [
        [InlineKeyboardButton(text="Sim", callback_data=str(RETURN))],
        [InlineKeyboardButton(text="Nao", callback_data=str(END))]
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(text=ask_new_product, reply_markup=keyboard)

    return ANOTHER_PRODUCT

async def return_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    context.user_data[START] = True
    await start(update, context)

    return SELECTING_ACTION

async def change_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    await select_category(update, context)

    return RETURN

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End Conversation by command."""
    await update.message.reply_text("Okay, bye.")
    return SELECTING_CATEGORY

#class TelegramBot():
#    def __init__(self, database) -> None:
#        database = database

# Pague uma breja
def main():
    application = Application.builder().token("6163736593:AAFRImnBRLZ3Ra7TRuECvoBT1juJQmNxUv8").build()

    add_product_conv = ConversationHandler(
        entry_points={
            CallbackQueryHandler(ask_for_product, pattern="^" + str(ELETRONICS) + "$|^" + str(OTHERS) + "$")
        },
        states={
            TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_product)],
            ANOTHER_PRODUCT: [
                CallbackQueryHandler(return_to_start, pattern="^" + str(END) + "$"),
                CallbackQueryHandler(select_category, pattern="^" + str(RETURN) + "$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(select_category, pattern="^" + str(RETURN) + "$"),
            CommandHandler("stop", stop)
        ],
        map_to_parent={
            RETURN: ADDING,
            ADDING: ADDING,
            SELECTING_ACTION: SELECTING_ACTION
        }
    )

    category_conv = ConversationHandler(
        entry_points={
            CallbackQueryHandler(select_category, pattern="^" + str(SELECTING_CATEGORY) + "$")
        },
        states={
            ADDING: [add_product_conv]
        },
        fallbacks=[
            CallbackQueryHandler(return_to_start, pattern="^" + str(END) + "$"),
            CommandHandler("stop", stop)
        ],
        map_to_parent={
            SELECTING_ACTION: SELECTING_ACTION
        }
    )

    selection_handlers = [
        category_conv,
        CallbackQueryHandler(donation, pattern="^" + str(DONATION) + "$"),
    ]
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SHOWING: [CallbackQueryHandler(start, pattern="^" + str(END) + "$")],
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