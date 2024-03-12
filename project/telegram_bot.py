import asyncio
import json
import logging
import os

import requests
from redis import Redis
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import NetworkError
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, ConversationHandler, MessageHandler,
                          filters)

from project import config
from project.database import Database
from project.metrics_collector import MetricsCollector
from project.models import FormatPromoMessage
from project.utils import brand_to_bot, normalize_str
from project.vectorizers import Vectorizers

# First Level
(
    SELECTING_ACTION, SELECTING_CATEGORY,
    TO_ADD, TO_LIST, ADD_BLACKLIST
) = map(chr, range(5))

# Second
ELETRONICS, CLOTHES, HOUSE, PETS, BOOKS, OTHERS = map(chr, range(5, 11))  # max 5 to 11 (6)

# Third
ANOTHER_PRODUCT = map(chr, range(11, 12))

STOPPING, SHOWING, TYPING, LISTING, PRICING, SKIP = map(chr, range(12, 18))

END = ConversationHandler.END

(
    START,
    DONATION,
    SHOW_DONATE,
    RETURN,
    INDEX
) = map(chr, range(19, 24))

BLOCK_STORES, SHOW_BLOCK = map(chr, range(25, 27))

# Monitoring funcs
class TelegramBot ():
    application: Application
    add_product_conv: ConversationHandler
    category_conv: ConversationHandler
    selection_handlers: ConversationHandler
    database: Database
    vectorizer: Vectorizers
    metrics_collector: MetricsCollector
    redis_client: Redis

    def __init__ (self, **kwargs) -> None:
        self.database = kwargs.get("database")
        self.vectorizer = kwargs.get("vectorizer")
        self.application = Application.builder().token(config.TELEGRAM_TOKEN).build()
        logging.warning("Ligando o troço")

        self.metrics_collector = kwargs.get("metrics_collector")
        self.redis_client = kwargs.get("redis_client")

        self.redis_client.set("send_first_promo", 1)

        self.block_stores_conv = ConversationHandler(
            entry_points={
                CallbackQueryHandler(self.list_stores, pattern="^" + str(TO_LIST) + "$")
            },
            states={
                LISTING: [
                    CallbackQueryHandler(self.return_to_start, pattern="^" + str(END) + "$"),
                    CallbackQueryHandler(self.block_store, pattern=r"^B\d*$")
                ]
            },
            fallbacks={
                CommandHandler("start", self.start),
                CommandHandler("help", self.show_help),
                CommandHandler("status", self.show_status)
            },
            map_to_parent={
                RETURN: SHOWING,
                ANOTHER_PRODUCT: SHOWING
            }
        )

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
                    ),
                    CallbackQueryHandler(
                        self.ask_for_blacklist, pattern="^" + str(RETURN) + r"$|^B\d*$"
                    ),
                    CallbackQueryHandler(
                        self.show_block_stores, pattern="^" + str(RETURN) + r"$|^A\d*$"
                    )
                ],
                PRICING: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.save_product)],
                TYPING: [
                    CallbackQueryHandler(self.save_blacklist, pattern="^" + str(RETURN)),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.save_blacklist)
                ],
                SHOW_BLOCK: [ self.block_stores_conv ]
            },
            fallbacks={
                CommandHandler("start", self.start),
                CommandHandler("help", self.show_help),
                CommandHandler("status", self.show_status)
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
                    self.ask_for_product,
                    pattern=f"^{ELETRONICS}$|^{CLOTHES}$|^{HOUSE}$|^{PETS}$|^{BOOKS}$|^{OTHERS}$"
                )
            },
            states={
                TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.save_price)],
                PRICING: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.save_product),
                    CallbackQueryHandler(self.save_product, pattern="^" + str(SKIP) + "$"),
                ],
                ANOTHER_PRODUCT: [
                    CallbackQueryHandler(self.select_category, pattern="^" + str(RETURN) + "$")
                ]
            },
            fallbacks=[
                CallbackQueryHandler(self.return_to_start, pattern="^" + str(END) + "$"),
                CallbackQueryHandler(self.select_category, pattern="^" + str(RETURN) + "$"),
                CommandHandler("start", self.start),
                CommandHandler("help", self.show_help),
                CommandHandler("status", self.show_status)
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
                TO_ADD: [ self.add_product_conv ]
            },
            fallbacks=[
                CallbackQueryHandler(self.return_to_start, pattern="^" + str(END) + "$"),
                CommandHandler("start", self.start),
                CommandHandler("help", self.show_help),
                CommandHandler("status", self.show_status)
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
            entry_points=[
                CommandHandler("start", self.start),
                CommandHandler("help", self.show_help),
                CommandHandler("status", self.show_status)
            ],
            states={
                SHOWING: [CallbackQueryHandler(self.start, pattern="^" + str(END) + "$")],
                SELECTING_ACTION: self.selection_handlers,
                STOPPING: [CommandHandler("start", self.start)]
            },
            fallbacks=[
                CommandHandler("start", self.start),
                CommandHandler("help", self.show_help),
                CommandHandler("status", self.show_status)
            ]
        )
        self.application.add_handler(handler=self.conv_handler)

    @classmethod
    async def enque_message (cls, context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str):
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=ParseMode.MARKDOWN_V2,
                disable_web_page_preview=False
            )

        except Exception:
            raise NetworkError("Erro ao enviar mensagem")

    async def show_help (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        await update.message.reply_text(
                    "O telepromobr é um bot de busca e alerta de ofertas!\n"
                    "Caso experiencie algum erro e/ou travamento durante a aplicação, por favor"
                    "utilize novamente o comando '/start' para retornar ao inicio.\n"
                    "Caso queira ver os sites que o bot procura, de '/status'\n"
                    "\n"
                    "Em caso de bugs ou problemas, relate a telepromobr@gmail.com\n"
                    "Por favor, se puder, de uma moral na aba 'Fortalecer Breja'\n"
                    "Obrigado por utilizar!"
            )

        context.user_data[START] = False
        await self.start(update, context)

        return SELECTING_ACTION

    async def show_status (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        site_status = self.database.get_site_status()
        await update.message.reply_text(f"Status de cada site do bot:\n{site_status}")

        context.user_data[START] = False
        await self.start(update, context)

        return SELECTING_ACTION

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
                    "Olá, eu sou o Bot TelePromoBr, "
                    "estou aqui para te ajudar a acompanhar preços/promoções de produtos"
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
            [InlineKeyboardButton(text="📱 - Eletronicos", callback_data=str(ELETRONICS))],
            [InlineKeyboardButton(text="👚 - Roupas", callback_data=str(CLOTHES))],
            [InlineKeyboardButton(text="🏠 - Casa/Lar", callback_data=str(HOUSE))],
            [InlineKeyboardButton(text="🐶 - Pets", callback_data=str(PETS))],
            [InlineKeyboardButton(text="📚 - Livros", callback_data=str(BOOKS))],
            [InlineKeyboardButton(text="📝 - Outros", callback_data=str(OTHERS))],
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
        context.user_data[TYPING] = update.callback_query.data
        context.user_data[INDEX] = None

        return TYPING

    async def save_price (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        product_ask = (
            "APENAS NUMEROS SEM VIRGULA. Digite '0' se não quiser limitar o preco\n"
            "(Limites de valores, exemplo: 200-1000 vai pegar de R$ 200 até R$ 1000)\n"
        )

        keyboard = None

        if context.user_data.get(TYPING, False):
            # Salvar produto no Mongo
            user_id = update.message.from_user["id"]
            user_name = update.message.from_user["first_name"]
            product = update.message.text
            tag_list = await self.vectorizer.extract_tags(product, "")
            tag_mapping = {
                ELETRONICS: "eletronics", CLOTHES: "clothes", HOUSE: "house",
                PETS: "pets", BOOKS: "books", OTHERS: "others"
            }
            category = tag_mapping[context.user_data[TYPING]]

            status, message = self.database.insert_new_user_wish(
                user_id, user_name, tag_list, product, category
            )

            if status:
                product_ask = (
                    "Adicionado! Deseja definir valores maximos para o produto?:\n"
                    + product_ask
                )
                button = InlineKeyboardButton(text="Pular", callback_data=str(SKIP))

                # Decrease in one edited
                self.metrics_collector.handle_user_request("new")

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

        else:
            option = update.callback_query.data
            if option and option.startswith("E") and option[1:].isdigit():
                context.user_data[INDEX] = int(option[1:])

            function = update.callback_query.edit_message_text

        await function(text=product_ask, reply_markup=keyboard)

        return PRICING

    async def save_product (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        index = context.user_data.get(INDEX)

        if index is not None:
            end_text = "Editado!"
            button = InlineKeyboardButton(text="Voltar", callback_data=str(RETURN))
            keyboard = InlineKeyboardMarkup.from_button(button)

            # Increase in one edited
            self.metrics_collector.handle_user_request("edit")

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

        if update.message is not None:
            values = update.message.text
            lower_price, max_price = ( None, None )
            hifens = values.count("-")

            user_id = update.message.from_user["id"]

            if not all(v.isnumeric() for v in values.split("-")) or hifens > 1:
                end_text = "Valor invalido, tentar novamente?"

            else:
                if hifens:
                    lower_price, max_price = tuple(map(int, values.split("-")))

                else:
                    max_price = values

                self.database.update_wish_by_index(
                    user_id, index, lower_price=lower_price, max_price=max_price
                )

        option = update.callback_query

        if option and option.data == SKIP:
            await update.callback_query.edit_message_text(text=end_text, reply_markup=keyboard)

        else:
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
            f"Maximo: {wish_obj['max']}\n"
            f"Minimo: {wish_obj['min']}\n"
            f"Blacklist: {wish_obj['blacklist']}\n"
        )

        buttons = [
            [
                InlineKeyboardButton(text="Remover", callback_data=f"R{index}"),
                InlineKeyboardButton(text="Mudar Preço", callback_data=f"E{index}")
            ],
            [ InlineKeyboardButton(text="Blacklist", callback_data=f"B{index}") ],
            # [ InlineKeyboardButton(text="Bloquear lojas", callback_data=f"A{index}") ],
            [ InlineKeyboardButton(text="Voltar", callback_data=str(RETURN)) ]
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

            # Decrease in one edited
            self.metrics_collector.handle_user_request("remove")

        await self.list_wishs(update, context)

        return LISTING

    async def return_to_start (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        context.user_data[START] = True
        await self.start(update, context)

        return SELECTING_ACTION

    async def ask_for_blacklist (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        new_product_text = (
            "Escreva abaixo as palavras que vão ser descartadas ao procurar produtos:\n"
        )

        button = InlineKeyboardButton(text="Remover blacklist (voltar)", callback_data=str(RETURN))
        keyboard = InlineKeyboardMarkup.from_button(button)

        await update.callback_query.edit_message_text(text=new_product_text, reply_markup=keyboard)

        context.user_data[START] = True
        option = update.callback_query.data
        if option and option.startswith("B") and option[1:].isdigit():
            context.user_data[INDEX] = int(option[1:])

        return TYPING

    async def save_blacklist (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        button = InlineKeyboardButton(text="Voltar", callback_data=str(RETURN))
        keyboard = InlineKeyboardMarkup.from_button(button)

        # User sent words to blacklist
        if update.message:
            blacklist_words = normalize_str(update.message.text).split(" ")
            user_id = update.message.from_user["id"]

            if blacklist_words == [""]:
                blacklist_words = []

            self.database.update_wish_by_index(
                user_id, context.user_data[INDEX], blacklist=blacklist_words
            )

            end_text = "Blacklist salva!"
            await update.message.reply_text(text=end_text, reply_markup=keyboard)

        else:
            end_text = "Blacklist não salva."

            await update.callback_query.edit_message_text(text=end_text, reply_markup=keyboard)

        return SHOWING

    async def show_block_stores (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        option = update.callback_query.data

        if option and option.startswith("A") and option[1:].isdigit():
            context.user_data[INDEX] = int(option[1:])

        return SHOW_BLOCK

    async def list_stores (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        buttons = [[]]
        user_id = context._user_id

        for idx, store in enumerate(brand_to_bot):
            last_line = buttons[-1]

            last_line.append(InlineKeyboardButton(text=store, callback_data=f"B{idx}"))

            if len(last_line) == 2:
                buttons.append([])

        buttons.append(InlineKeyboardButton(text="Voltar", callback_data=str(END)))

        return LISTING

    async def block_store (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        option = update.callback_query.data

        if option and option.startswith("B") and option[1:].isdigit():
            store_index = int(option[1:])
            store = list(brand_to_bot)[store_index]

        return RETURN

class ImportantJobs:
    repeating_jobs: list[str]
    redis_client: Redis

    ONE_DAY: int = 86400

    def __init__(self, redis_client: Redis) -> None:
        self.redis_client = redis_client
        self.repeating_jobs = [ "get_messages_and_send" ]

    # Tirar daqui depois "ah mas faz agr e bota em ingles"
    # Nao, meu codigo minhas regras.
    async def get_messages_and_send (self, context: ContextTypes.DEFAULT_TYPE):
        while True:
            raw_data = self.redis_client.lpop("msgs_to_send")

            if not raw_data:
                break

            data = json.loads(raw_data)
            chat_id = data["chat_id"]
            message = data["message"]

            await TelegramBot.enque_message(context, chat_id, message)
            await asyncio.sleep(0.1)

    async def sent_ngrok_msg (self, context: ContextTypes.DEFAULT_TYPE):
        try:
            ngrok_url = os.environ.get("NGROK_URL", "ngrok-docker")
            ngrok_servers = requests.get(f"http://{ngrok_url}:4040/api/tunnels").json()

            public_url = ngrok_servers["tunnels"][0]["public_url"]
            message = f"ngrok url:\n\n{public_url}"
            beautiful_msg = FormatPromoMessage.escape_msg(message)
            await TelegramBot.enque_message(context, config.BOT_OWNER_CHAT_ID, beautiful_msg)

            logging.warning(f"public_url {public_url}")

        except:
            logging.warning("Ngrok not setted")

    async def reset_default_promo (self, context: ContextTypes.DEFAULT_TYPE):
        self.redis_client.set("sent_first_promo", 1)

    async def reset_daily_promos (self):
        self.redis_client.set("reset_daily", 1)
