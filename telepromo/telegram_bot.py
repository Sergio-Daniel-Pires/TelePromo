import asyncio

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

import logging

import asyncio
from database import Database
from vectorizers import Vectorizers

# First Level
SELECTING_ACTION, SELECTING_CATEGORY, TO_ADD, TO_LIST = map(chr, range(4))

# Second
ELETRONICS, OTHERS = map(chr, range(4, 6))

# Third
ANOTHER_PRODUCT = map(chr, range(7, 8))

STOPPING, SHOWING, TYPING, LISTING,  = map(chr, range(10, 14))

END = ConversationHandler.END

(
    START,
    DONATION,
    SHOW_DONATE,
    RETURN
) = map(chr, range(12, 16))

# Monitoring funcs
class TelegramBot ():
    application: Application
    add_product_conv: ConversationHandler
    category_conv: ConversationHandler
    selection_handlers: ConversationHandler
    database: Database
    vectorizer: Vectorizers

    def __init__ (self, **kwargs) -> None:
        self.database = kwargs.get("database")
        self.vectorizer = kwargs.get("vectorizer")
        self.application = Application.builder().token("6163736593:AAFRImnBRLZ3Ra7TRuECvoBT1juJQmNxUv8").build()

        self.list_product_conv = ConversationHandler(
            entry_points={
                CallbackQueryHandler(self.list_wishs, pattern="^" + str(TO_LIST) + "$")
            },
            states={
                LISTING: [
                    CallbackQueryHandler(self.return_to_start, pattern="^" + str(END) + "$"),
                    CallbackQueryHandler(self.product_details, pattern="^W\d*$")
                ],
                SHOWING: [
                    CallbackQueryHandler(self.return_to_product_list, pattern="^" + str(RETURN) + "$|^R\d*$")
                ]
            },
            fallbacks={
                CommandHandler("stop", self.stop)
            },
            map_to_parent={
                SELECTING_ACTION: SELECTING_ACTION
            }
        )
        self.add_product_conv = ConversationHandler(
            entry_points={
                CallbackQueryHandler(self.ask_for_product, pattern="^" + str(ELETRONICS) + "$|^" + str(OTHERS) + "$")
            },
            states={
                TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.save_product)],
                ANOTHER_PRODUCT: [
                    CallbackQueryHandler(self.return_to_start, pattern="^" + str(END) + "$"),
                    CallbackQueryHandler(self.select_category, pattern="^" + str(RETURN) + "$")
                ]
            },
            fallbacks=[
                CallbackQueryHandler(self.select_category, pattern="^" + str(RETURN) + "$"),
                CommandHandler("stop", self.stop)
            ],
            map_to_parent={
                RETURN: TO_ADD,
                TO_ADD: TO_ADD,
                SELECTING_ACTION: SELECTING_ACTION
            }
        )
        self.category_conv = ConversationHandler(
            entry_points={
                CallbackQueryHandler(self.select_category, pattern="^" + str(SELECTING_CATEGORY) + "$")
            },
            states={
                TO_ADD: [self.add_product_conv]
            },
            fallbacks=[
                CallbackQueryHandler(self.return_to_start, pattern="^" + str(END) + "$"),
                CommandHandler("stop", self.stop)
            ],
            map_to_parent={
                SELECTING_ACTION: SELECTING_ACTION
            }
        )

        self.selection_handlers = [
            self.category_conv,
            self.list_product_conv,
            CallbackQueryHandler(self.donation, pattern="^" + str(DONATION) + "$"),
        ]
        self.conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={
                SHOWING: [CallbackQueryHandler(self.start, pattern="^" + str(END) + "$")],
                SELECTING_ACTION: self.selection_handlers,
                STOPPING: [CommandHandler("start", self.start)]
            },
            fallbacks=[
                CommandHandler("stop", self.stop)
            ]
        )
        self.application.add_handler(handler=self.conv_handler)

    async def iniatilize (self):
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()

    async def send_message (self, chat_id, text):
        await self.application.bot.sendMessage(chat_id=chat_id, text=text)

    async def start (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Select an action: Donation, Finalize, List wishs, New Wish"""
        text = (
            "Escolha uma dos botões abaixo:\n"
            "ou\n"
            "Para abrir menu ajuda: /help\n"
        )

        buttons = [
            [InlineKeyboardButton(text="Fortalecer Breja", callback_data=str(DONATION))],
            [InlineKeyboardButton(text="Novo produto", callback_data=str(SELECTING_CATEGORY))],
            [InlineKeyboardButton(text="Lista de Desejos", callback_data=str(TO_LIST))],
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

    async def donation (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
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

    async def select_category (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
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

        return TO_ADD

    async def ask_for_product (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        new_product_text = (
            "Escreva abaixo o nome do produto:\n"
        )
        button = InlineKeyboardButton(text="Voltar", callback_data=str(RETURN))
        keyboard = InlineKeyboardMarkup.from_button(button)
        await update.callback_query.edit_message_text(text=new_product_text, reply_markup=keyboard)

        context.user_data[START] = True

        return TYPING

    async def save_product (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        # Salvar produto no Mongo
        user_id = update.message.from_user["id"]
        product = update.message.text
        tag_list = self.vectorizer.extract_tags(product)

        status, message = self.database.insert_new_user_wish(user_id, tag_list, product, self.vectorizer.categorys.ELETRONICS.value)
        buttons = [
            [InlineKeyboardButton(text="Sim", callback_data=str(RETURN))],
            [InlineKeyboardButton(text="Nao", callback_data=str(END))]
        ]
        # Adicionado com sucesso
        if status:
            ask_new_product = (
                    "Adicionado! Deseja adicionais mais?"
                )
        else:
            if message == "Usuário só pode ter até 10 wishes":
                ask_new_product = message

                buttons = [
                    [InlineKeyboardButton(text="Inicio", callback_data=str(END))]
                ]
            else:
                ask_new_product = (
                    message + "\n"
                    "Deseja tentar novamente?"
                )
        keyboard = InlineKeyboardMarkup(buttons)
        await update.message.reply_text(text=ask_new_product, reply_markup=keyboard)

        return ANOTHER_PRODUCT

    async def list_wishs (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        buttons = []

        user_id = context._user_id
        wish_list = self.database.user_wishes(user_id)
        if len(wish_list) == 0:
            list_wish_text = (
                "Você ainda não tem alertas!\n"
                "Crie alertas na aba 'Adicionar produtos'!"
            )

        else:
            list_wish_text = "Seus alertas:"
            for index, wish_obj in enumerate(wish_list):
                name = wish_obj["name"]
                buttons.append([InlineKeyboardButton(text=name, callback_data=f"W{index}")])

        buttons.append([InlineKeyboardButton(text="Inicio", callback_data=str(END))])
        keyboard = InlineKeyboardMarkup(buttons)
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=list_wish_text, reply_markup=keyboard)

        return LISTING

    async def product_details (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        option = update.callback_query.data
        user_id = context._user_id
        index = int(option[1:])
        wish_obj = self.database.user_wishes(user_id)[index]
        product_text = (
            f"Produto: {wish_obj['name']}"
        )
        buttons = [
            [InlineKeyboardButton(text="Remover", callback_data=f"R{index}")],
            [InlineKeyboardButton(text="Voltar", callback_data=str(RETURN))]
        ]
        keyboard = InlineKeyboardMarkup(buttons)

        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=product_text, reply_markup=keyboard)

        return SHOWING

    async def return_to_product_list (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        option = update.callback_query.data
        if option.startswith("R") and option[1:].isdigit():
            user_id = context._user_id
            index = int(option[1:])
            wish_obj = self.database.user_wishes(user_id)[index]
            self.database.remove_user_wish(user_id, wish_obj=wish_obj)

        await self.list_wishs(update, context)

        return LISTING

    async def return_to_start (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        context.user_data[START] = True
        await self.start(update, context)

        return SELECTING_ACTION

    async def stop (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """End Conversation by command."""
        await update.message.reply_text("Okay, bye.")
        return SELECTING_CATEGORY

async def main ():
    telebot = TelegramBot("")
    await telebot.iniatilize()

    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
