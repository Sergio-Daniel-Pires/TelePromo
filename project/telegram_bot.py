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
from project.models import FormatPromoMessage, User
from project.utils import normalize_str
from project.vectorizers import Vectorizers

# Action handles
(
    SHOWING, SELECTING_ACTION, TYPING, RETURN,
    RETURN_TO, ADD_MORE, TRY_AGAIN, SKIP, INDEX
) = range(1, 10)

# First level
(
    START, DONATION, DETAILING, SELECTING_CATEGORY, TO_LIST, TO_ADD_NEW, TO_WISH, EDIT_PRICE
) = range(11, 19)

# Second level
PRICING, DEL_BLACKLIST, CHANGING_BLACKLIST, LISTING, FINISHING = range(20, 25)

# Category const types
ELETRONICS, CLOTHES, HOUSE, PETS, BOOKS, OTHERS = range(26, 32)

END = ConversationHandler.END

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

        self.donation_conv = ConversationHandler(
            entry_points=[ CallbackQueryHandler(self.donation, pattern=f"^{DONATION}$") ],
            states={ SHOWING: [ CallbackQueryHandler(self.default_options, f"^{RETURN}$") ] },
            fallbacks=[
                CallbackQueryHandler(self.end_conversation, f"^{SELECTING_ACTION}$")
            ],
            map_to_parent={ SELECTING_ACTION: SELECTING_ACTION }
        )

        self.wish_list_conv = ConversationHandler(
            entry_points=[ CallbackQueryHandler(self.list_wishes, pattern=f"^{TO_LIST}$") ],
            states={
                LISTING: [
                    # Return to Top Level
                    CallbackQueryHandler(self.default_options, pattern=f"^{RETURN}$"),
                    CallbackQueryHandler(self.wish_details, pattern=f"^W[0-9]*$")
                ],
                DETAILING: [
                    # Return to LISTING
                    CallbackQueryHandler(self.list_wishes, pattern=f"^{RETURN}$"),
                    CallbackQueryHandler(self.delete_wish, pattern=f"^D[0-9]*$"),

                    # Later, return for same product
                    CallbackQueryHandler(self.change_blacklist, pattern=f"^CB[0-9]*$"),
                ],
                CHANGING_BLACKLIST: [
                    CallbackQueryHandler(
                        self.confirm_bl_change, pattern=f"^{DEL_BLACKLIST}$|^{RETURN}$"
                    ),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.confirm_bl_change)
                ]
            },
            fallbacks=[
                CallbackQueryHandler(self.end_conversation, f"^{SELECTING_ACTION}$")
            ],
            map_to_parent={ SELECTING_ACTION: SELECTING_ACTION }
        )

        self.add_wish_conv = ConversationHandler(
            entry_points=[ CallbackQueryHandler(self.select_category, pattern=f"^{TO_ADD_NEW}$") ],
            states={
                SELECTING_CATEGORY: [
                    #Return to Top Level
                    CallbackQueryHandler(self.default_options, pattern=f"^{RETURN}$"),
                    CallbackQueryHandler(
                        self.show_product_msg,
                        pattern=f"^({ELETRONICS}|{CLOTHES}|{HOUSE}|{PETS}|{BOOKS}|{OTHERS})$"
                    )
                ],
                TYPING: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.verify_save_product),
                    # Return to select category
                    CallbackQueryHandler(self.select_category, pattern=f"^{RETURN}$")
                ],
                PRICING: [
                    CallbackQueryHandler(self.verify_price, pattern=f"^{SKIP}$"),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.verify_price)
                ],
                TO_ADD_NEW: [
                    CallbackQueryHandler(self.select_category, pattern=f"^{ADD_MORE}$"),
                    CallbackQueryHandler(self.default_options, pattern=f"^{SELECTING_ACTION}$")
                ]
            },
            fallbacks=[
                CallbackQueryHandler(self.end_conversation, f"^{SELECTING_ACTION}$")
            ],
            map_to_parent={ SELECTING_ACTION: SELECTING_ACTION }
        )

        self.conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("start", self.default_options)
            ],
            states={
                SELECTING_ACTION: [ self.donation_conv, self.add_wish_conv, self.wish_list_conv ],
            },
            fallbacks=[]
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

    async def donation (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """View the donations method and return"""
        donation_text = (
            "O criador desse bot é o Sérgio Pires "
            "[Meu GitHub](https://github.com/Sergio-Daniel-Pires)\n"
            "Caso queira me pagar uma breja🍻, pode mandar um PIX para:\n\n"
            r"telepromobr@gmail\.com"
        )

        button = InlineKeyboardButton(text="Inicio", callback_data=RETURN)
        keyboard = InlineKeyboardMarkup.from_button(button)

        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=donation_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN_V2
        )

        return SHOWING

    async def default_options (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Select an action: Donation, Finalize, List wishs, New Wish"""
        text = (
            "Escolha uma dos botões abaixo:\n"
            "ou\n"
            "Para abrir menu ajuda: /help\n"
        )

        buttons = [
            [InlineKeyboardButton(text="🍻 - Fortalecer Breja", callback_data=DONATION)],
            [InlineKeyboardButton(text="➕ - Novo produto", callback_data=TO_ADD_NEW)],
            [InlineKeyboardButton(text="📝 - Lista de Desejos", callback_data=TO_LIST)],
        ]
        keyboard = InlineKeyboardMarkup(buttons)

        context.user_data[INDEX] = None

        if update.message is not None:
            await update.message.reply_text(
                    "Olá, eu sou o Bot TelePromoBr, "
                    "estou aqui para te ajudar a acompanhar preços/promoções de produtos"
            )
            await update.message.reply_text(text=text, reply_markup=keyboard)

        else:
            await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

        return SELECTING_ACTION

    async def end_conversation (self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return SELECTING_ACTION

    async def list_wishes (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        buttons = []

        user_id = context._user_id

        user_obj = self.database.find_user(user_id)

        if user_obj is None:
            list_wish_text = "Você ainda não usou os serviços!\n"

        else:
            user_obj = User.from_dict(user_obj)
            wish_list = self.database.user_wishes(user_id, user_obj.name)

            if len(wish_list) == 0:
                list_wish_text = (
                    "Você ainda não tem alertas!\n"
                    "Crie alertas na aba 'Adicionar produtos'!"
                )

            else:
                list_wish_text = "Seus alertas:"

                for index, wish_obj in enumerate(wish_list):
                    buttons.append([
                        InlineKeyboardButton(text=wish_obj.name, callback_data=f"W{index}")
                    ])

        buttons.append([InlineKeyboardButton(text="Inicio", callback_data=RETURN)])
        keyboard = InlineKeyboardMarkup(buttons)

        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=list_wish_text, reply_markup=keyboard)

        return LISTING

    async def select_category (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Add new product"""
        select_category_text = (
            "Selecione a categoria do produto:\n"
        )

        buttons = [
            [InlineKeyboardButton(text="📱 - Eletronicos", callback_data=ELETRONICS)],
            [InlineKeyboardButton(text="👚 - Roupas", callback_data=CLOTHES)],
            [InlineKeyboardButton(text="🏠 - Casa/Lar", callback_data=HOUSE)],
            [InlineKeyboardButton(text="🐶 - Pets", callback_data=PETS)],
            [InlineKeyboardButton(text="📚 - Livros", callback_data=BOOKS)],
            [InlineKeyboardButton(text="📝 - Outros", callback_data=OTHERS)],
            [InlineKeyboardButton(text="Inicio", callback_data=RETURN)]
        ]

        keyboard = InlineKeyboardMarkup(buttons)

        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=select_category_text, reply_markup=keyboard
        )

        return SELECTING_CATEGORY

    async def show_product_msg (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        new_product_text = "Escreva abaixo o nome do produto:\n"

        # If was coming from "Select Category"
        if update.callback_query:
            context.user_data[SELECTING_CATEGORY] = update.callback_query.data

        button = InlineKeyboardButton(text="Voltar", callback_data=RETURN)
        keyboard = InlineKeyboardMarkup.from_button(button)

        if update.callback_query is not None:
            await update.callback_query.edit_message_text(
                text=new_product_text, reply_markup=keyboard
            )

        else:
            await update.message.reply_text(text=new_product_text, reply_markup=keyboard)

        return TYPING

    async def verify_save_product (self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.message.from_user["id"]
        user_name = update.message.from_user["first_name"]
        raw_product_name = update.message.text
        has_inserted, message = await self.prepare_and_insert_wish(
            raw_product_name, context.user_data[SELECTING_CATEGORY], user_id, user_name
        )

        # Funcionou, deve esperar texto
        if has_inserted:
            # Index are -1 if has inserted
            context.user_data[INDEX] = -1
            message += " Deseja adicionar limites de valores?"
            await update.message.reply_text(message)

            # Jump directly to price_conv
            return await self.show_price_message(update, context)

        # Falhou, deve voltar para o "TYPING" ou para começo, caso seja erro de limite
        else:
            if message == "Usuário só pode ter até 10 wishes":
                await update.message.reply_text(message)

                # Return for initial menu
                return await self.default_options(update, context)

            else:
                message += " Por favor, tente novamente."
                await update.message.reply_text(message)

                # On error, return directly to TYPING
                return await self.show_product_msg(update, context)

    async def show_price_message (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        price_text = (
            "APENAS NUMEROS SEM VIRGULA. Digite '0' ou 'Pular' não quiser limitar o preco\n"
            "(Limites de valores, exemplo: 200-1000 vai pegar de R$ 200 até R$ 1000)\n"
        )
        button = InlineKeyboardButton(text="Pular", callback_data=SKIP)
        keyboard = InlineKeyboardMarkup.from_button(button)

        await update.message.reply_text(price_text, reply_markup=keyboard)

        return PRICING

    async def verify_price (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        price_range = "0"
        index = context.user_data.get(INDEX) or -1
        user_id = context._user_id

        # Option is None when comes from user text input
        if update.callback_query is None:
            price_range = update.message.text

        is_price_range_ok = self.split_and_insert_price_range(price_range, user_id, index)

        if not is_price_range_ok:
            invalid_price_error = "Valor invalido, Por favor, tente novamente"

            await update.message.reply_text(text=invalid_price_error)

            # Return to PRICING
            return await self.show_price_message(update, context)

        # TODO find best way to do this handler dynamic
        if index == -1: # Case from add new product
            message = "Preço salvo com sucesso!"
            if update.message is not None:
                await update.message.reply_text(message)

            else:
                await update.callback_query.edit_message_text(message)

            return await self.ask_for_add_more(update, context)

    async def ask_for_add_more (self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = "Gostaria de adicionar mais produtos?"

        buttons = [ [
            InlineKeyboardButton(text="Sim", callback_data=ADD_MORE),
            InlineKeyboardButton(text="Nao", callback_data=SELECTING_ACTION)
        ] ]
        keyboard = InlineKeyboardMarkup(buttons)

        if update.message is not None:
            await update.message.reply_text(message, reply_markup=keyboard)

        else:
            await update.callback_query.edit_message_text(message, reply_markup=keyboard)

        return TO_ADD_NEW

    async def wish_details (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        user_id = context._user_id

        # INDEX, when returning from blacklist change or option when comes from wish list
        index = context.user_data.get(INDEX)
        if index is None:
            index = int(update.callback_query.data[1:])
            context.user_data[INDEX] = index

        user_obj = User.from_dict(self.database.find_user(user_id))

        logging.info(self.database.user_wishes(user_id, user_obj.name))
        wish_obj = self.database.user_wishes(user_id, user_obj.name)[index]

        product_text = (
            f"Produto: {wish_obj.name}\n"
            f"Filtro de Preço: {wish_obj.min}-{wish_obj.max}\n"
            f"Blacklist: {wish_obj.blacklist}\n"
        )

        buttons = [
            [
                InlineKeyboardButton(text="Remover", callback_data=f"D{index}"),
                InlineKeyboardButton(text="Mudar Preço", callback_data=f"E{index}")
            ],
            [ InlineKeyboardButton(text="Editar Blacklist", callback_data=f"CB{index}") ],
            # [ InlineKeyboardButton(text="Bloquear lojas", callback_data=f"A{index}") ],
            # TODO good feature, remembers me too add later.
            [ InlineKeyboardButton(text="Voltar", callback_data=RETURN) ]
        ]
        keyboard = InlineKeyboardMarkup(buttons)

        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=product_text, reply_markup=keyboard)

        return DETAILING

    async def delete_wish (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        option = update.callback_query.data

        self.database.remove_user_wish(context._user_id, int(option[1:]))

        # Decrease in one edited
        self.metrics_collector.handle_user_request("remove")

        # Directly returning for list wishes
        context.user_data[INDEX] = None # BUG Don't remove this line or index detailing gonna crazy
        return await self.list_wishes(update, context)

    async def change_blacklist (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        new_product_text = (
            "Escreva abaixo as palavras que vão ser descartadas ao procurar produtos:\n"
        )

        buttons = [ [
            InlineKeyboardButton(text="Voltar", callback_data=RETURN),
            InlineKeyboardButton(text="Remover blacklist", callback_data=DEL_BLACKLIST)
        ] ]

        context.user_data[INDEX] = int(update.callback_query.data[2:])

        keyboard = InlineKeyboardMarkup(buttons)

        await update.callback_query.edit_message_text(text=new_product_text, reply_markup=keyboard)

        return CHANGING_BLACKLIST

    async def confirm_bl_change (self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        option = update.callback_query.data

        if option != RETURN:
            # Or update blacklist from message or remove
            if update.message is not None:
                blacklist = normalize_str(update.message.text).split(" ")

                if blacklist == [ "" ]:
                    blacklist = []

            else:
                blacklist = []

            self.database.update_wish_by_index(
                context._user_id, context.user_data[INDEX], blacklist=blacklist
            )

        # Directly returning for wish detail
        return await self.wish_details(update, context)

    async def prepare_and_insert_wish (
        self, raw_product_name: str, category_type: str, user_id: int, user_name: str,
    ) -> tuple[bool, str]:
        """
        return true if was inserted new wish or false with reason.
        """
        tag_list = await self.vectorizer.extract_tags(raw_product_name)

        tag_mapping = {
            ELETRONICS: "eletronics", CLOTHES: "clothes", HOUSE: "house",
            PETS: "pets", BOOKS: "books", OTHERS: "others"
        }
        category = tag_mapping[int(category_type)]

        has_inserted, message = self.database.insert_new_user_wish(
            user_id, user_name, tag_list, raw_product_name, category
        )

        return has_inserted, message

    def split_and_insert_price_range (self, price_range: str, user_id: int, index: int) -> bool:
        min_price, max_price = ( None, None )
        price_range = [
            int(x) for x in price_range.split("-") if price_range.count("-") <= 1 and x.isnumeric()
        ]

        if len(price_range) == 0 or len(price_range) > 2:
            return False

        max_price = price_range[0]
        min_price = 0

        if len(price_range) == 2:
            min_price, max_price = price_range

        self.database.update_wish_by_index(
            user_id, index, min_price=min_price, max_price=max_price
        )

        return True

class ImportantJobs:
    repeating_jobs: list[str]
    redis_client: Redis

    def __init__(self, redis_client: Redis) -> None:
        self.redis_client = redis_client
        self.repeating_jobs = [ "get_messages_and_send" ]

    async def get_messages_and_send (self, context: ContextTypes.DEFAULT_TYPE):
        """
        Get messages from redis and send to users
        """
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
        """
        Sent ngrok url link to bot owner if ngrok was setted
        """
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
        """
        Sent ngrok message link to bot owner every day
        """
        self.redis_client.set("sent_first_promo", 1)
