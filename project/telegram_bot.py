import asyncio

from project.database import Database
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, ConversationHandler, MessageHandler,
                          filters)
from telegram.constants import ParseMode
from project.vectorizers import Vectorizers

# First Level
SELECTING_ACTION, SELECTING_CATEGORY, TO_ADD, TO_LIST = map(chr, range(4))

# Second
ELETRONICS, LAR, OTHERS = map(chr, range(4, 7))  # max 4 to 10 (6)

# Third
ANOTHER_PRODUCT = map(chr, range(10, 11))

STOPPING, SHOWING, TYPING, LISTING, PRICING = map(chr, range(11, 16))

END = ConversationHandler.END

(
    START,
    DONATION,
    SHOW_DONATE,
    RETURN,
    INDEX
) = map(chr, range(16, 21))

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
        self.application = Application.builder().token(
            "6163736593:AAFRImnBRLZ3Ra7TRuECvoBT1juJQmNxUv8"
        ).build()

        self.list_product_conv = ConversationHandler(
            entry_points={
                CallbackQueryHandler(self.list_wishs, pattern="^" + str(TO_LIST) + "$")
            },
            states={
                LISTING: [
                    CallbackQueryHandler(self.return_to_start, pattern="^" + str(END) + "$"),
                    CallbackQueryHandler(self.product_details, pattern=r"^W\d*$")
                ],
                SHOWING: [
                    CallbackQueryHandler(
                        self.return_to_product_list, pattern="^" + str(RETURN) + r"$|^R\d*$"
                    ),
                    CallbackQueryHandler(
                        self.save_price, pattern="^" + str(RETURN) + r"$|^E\d*$"
                    )
                ],
                PRICING: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.save_product)]
            },
            fallbacks={
                CommandHandler("start", self.start)
            },
            map_to_parent={
                SELECTING_ACTION: SELECTING_ACTION,
                RETURN: SHOWING,
                ANOTHER_PRODUCT: SHOWING
            }
        )

        self.add_product_conv = ConversationHandler(
            entry_points={
                CallbackQueryHandler(
                    self.ask_for_product, pattern="^" + str(ELETRONICS) + "$|^" + str(OTHERS) + "$"
                )
            },
            states={
                TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.save_price)],
                PRICING: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.save_product)],
                ANOTHER_PRODUCT: [
                    CallbackQueryHandler(self.return_to_start, pattern="^" + str(END) + "$"),
                    CallbackQueryHandler(self.select_category, pattern="^" + str(RETURN) + "$")
                ]
            },
            fallbacks=[
                CallbackQueryHandler(self.select_category, pattern="^" + str(RETURN) + "$"),
                CommandHandler("start", self.start)
            ],
            map_to_parent={
                RETURN: TO_ADD,
                TO_ADD: TO_ADD,
                SELECTING_ACTION: SELECTING_ACTION
            }
        )

        self.category_conv = ConversationHandler(
            entry_points={
                CallbackQueryHandler(
                    self.select_category, pattern="^" + str(SELECTING_CATEGORY) + "$"
                )
            },
            states={
                TO_ADD: [self.add_product_conv]
            },
            fallbacks=[
                CallbackQueryHandler(self.return_to_start, pattern="^" + str(END) + "$"),
                CommandHandler("start", self.start)
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
                CommandHandler("start", self.start)
            ]
        )
        self.application.add_handler(handler=self.conv_handler)

    async def iniatilize (self):
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()

    async def send_message (self, chat_id: int, text: str):
        await self.application.bot.sendMessage(
            chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=False
        )

    async def start (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Select an action: Donation, Finalize, List wishs, New Wish"""
        text = (
            "Escolha uma dos botões abaixo:\n"
            "ou\n"
            "Para abrir menu ajuda: /help\n"
        )

        buttons = [
            [InlineKeyboardButton(text="🍻 - Fortalecer Breja", callback_data=str(DONATION))],
            [InlineKeyboardButton(text="➕ - Novo produto", callback_data=str(SELECTING_CATEGORY))],
            [InlineKeyboardButton(text="📝 - Lista de Desejos", callback_data=str(TO_LIST))],
        ]
        keyboard = InlineKeyboardMarkup(buttons)

        if not context.user_data.get(START):
            await update.message.reply_text(
                (
                    "Olá, eu sou o Bot TelePromoBr, "
                    "estou aqui para te ajudar a acompanhar preços/promoções de produtos"
                )
            )
            await update.message.reply_text(text=text, reply_markup=keyboard)

        else:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)


        context.user_data[START] = False

        return SELECTING_ACTION

    async def donation (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """View the donations method and return"""
        donation_text = (
            "O criador desse bot é o Sérgio Pires @github\n"
            "Caso queira me pagar uma breja🍻, pode mandar um PIX para:\n\n"
            "telepromobr@gmail.com"
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
        await update.callback_query.edit_message_text(
            text=select_category_text, reply_markup=keyboard
        )

        return TO_ADD

    async def ask_for_product (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        new_product_text = (
            "Escreva abaixo o nome do produto:\n"
        )

        button = InlineKeyboardButton(text="Voltar", callback_data=str(RETURN))
        keyboard = InlineKeyboardMarkup.from_button(button)

        await update.callback_query.edit_message_text(text=new_product_text, reply_markup=keyboard)

        context.user_data[START] = True
        context.user_data[TYPING] = True
        context.user_data[INDEX] = False

        return TYPING

    async def save_price (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        product_ask = (
            "(APENAS NUMEROS, Digite '0' se não quiser limitar o preco):\n"
        )

        keyboard = None

        if update.callback_query:
            option = update.callback_query.data
            if option and option.startswith("E") and option[1:].isdigit():
                context.user_data[INDEX] = int(option[1:])

            function = update.callback_query.edit_message_text

        if context.user_data.get(TYPING, False):
            # Salvar produto no Mongo
            user_id = update.message.from_user["id"]
            user_name = update.message.from_user["first_name"]
            product = update.message.text
            tag_list = self.vectorizer.extract_tags(product, "")

            status, message = self.database.insert_new_user_wish(
                user_id, user_name, tag_list, product, "eletronics"
            )

            if status:
                product_ask = (
                    "Adicionado! Deseja definir um valor maximo para o produto?:\n"
                    + product_ask
                )
                button = InlineKeyboardButton(text="Pular", callback_data=str(END))

            else:
                if message == "Usuário só pode ter até 10 wishes":
                    product_ask = message

                    button = InlineKeyboardButton(text="Inicio", callback_data=str(END))

                else:
                    product_ask = (
                        message + "\n"
                        "Deseja tentar novamente?"
                    )
                    button = InlineKeyboardButton(text="Sim", callback_data=str(RETURN))

            function = update.message.reply_text

            keyboard = InlineKeyboardMarkup.from_button(button)

        await function(text=product_ask, reply_markup=keyboard)

        return PRICING

    async def save_product (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        value = update.message.text
        user_id = update.message.from_user["id"]

        if context.user_data.get(INDEX, False):
            index = context.user_data[INDEX]
            end_text = "Editado!"
            button = InlineKeyboardButton(text="Voltar", callback_data=str(RETURN))
            keyboard = InlineKeyboardMarkup.from_button(button)

            status_to_return = SHOWING

        else:
            index = -1

            end_text = "Finalizado! Gostaria de adicionar mais?"

            buttons = [
                [InlineKeyboardButton(text="Sim", callback_data=str(RETURN))],
                [InlineKeyboardButton(text="Nao", callback_data=str(END))]
            ]

            # Adicionado com sucesso
            keyboard = InlineKeyboardMarkup(buttons)

            status_to_return = ANOTHER_PRODUCT

        if not value.isnumeric():
            end_text = "Valor invalido, gostaria de tentar novamente?"
        else:
            self.database.update_wish_by_index(user_id, value, index)

        await update.message.reply_text(text=end_text, reply_markup=keyboard)

        return status_to_return

    async def list_wishs (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        buttons = []

        user_id = context._user_id

        user_obj = self.database.find_user(user_id)

        if not user_obj:
            list_wish_text = (
                "Você ainda não usou os serviços!\n"
            )

        else:
            user_name = user_obj["name"]
            wish_list = self.database.user_wishes(user_id, user_name)

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

                context.user_data[TYPING] = False

        buttons.append([InlineKeyboardButton(text="Inicio", callback_data=str(END))])
        keyboard = InlineKeyboardMarkup(buttons)

        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=list_wish_text, reply_markup=keyboard)

        return LISTING

    async def product_details (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        option = update.callback_query.data
        user_id = context._user_id
        index = int(option[1:])
        user_obj = self.database.find_user(user_id)
        user_name = user_obj["name"]

        wish_obj = self.database.user_wishes(user_id, user_name)[index]

        product_text = (
            f"Produto: {wish_obj['name']}\n"
            f"Maximo: {wish_obj['max']}"
        )

        buttons = [
            [
                InlineKeyboardButton(text="Remover", callback_data=f"R{index}"),
                InlineKeyboardButton(text="Editar", callback_data=f"E{index}")
            ],
            [InlineKeyboardButton(text="Voltar", callback_data=str(RETURN))]
        ]
        keyboard = InlineKeyboardMarkup(buttons)

        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=product_text, reply_markup=keyboard)

        return SHOWING

    async def return_to_product_list (
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> str:
        option = update.callback_query.data

        if option.startswith("R") and option[1:].isdigit():
            user_id = context._user_id
            index = int(option[1:])
            self.database.remove_user_wish(user_id, index)

        await self.list_wishs(update, context)

        return LISTING

    async def return_to_start (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        context.user_data[START] = True
        await self.start(update, context)

        return SELECTING_ACTION

async def main ():
    db = Database()
    vectorizers = Vectorizers()
    telebot = TelegramBot(
        database=db,
        vectorizer=vectorizers
    )
    await telebot.iniatilize()

    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
