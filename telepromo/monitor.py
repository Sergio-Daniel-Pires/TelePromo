import importlib
import logging
import datetime
import json
from typing import List

from models import Product, Price
from database import Database
from vectorizers import Vectorizers
from telegram_bot import TelegramBot

MINIMUN_DISCOUNT = 0.05

class Monitoring(object):
    """
    Class to monitoring sites in url
    """
    database: Database
    vectorizer: Vectorizers
    telegram_bot: TelegramBot

    def __init__(self, **kwargs):
        self.retry = kwargs.get("retrys")
        self.database = kwargs.get("database")
        self.vectorizer = kwargs.get("vectorizer")
        self.telegram_bot = kwargs.get("telegram_bot")

    async def prices_from_url(self, urls: List[dict]) -> list:
        """
        Get a URL and return the dict with prices
        """
        all_results = []
        for url in urls:
            link = url["link"]
            bot_name = url["name"]
            if link == "":
                logging.warn(f"{bot_name} não tem link, skipando...")
                continue

            bot_module = importlib.import_module(f"bots.{bot_name}")
            bot_class = getattr(bot_module, bot_name)
            bot_instance = bot_class()
            results = await bot_instance.run(link=link)
            all_results += results

        return all_results

    async def verify_save_prices(self, results: dict):
        today = datetime.datetime.utcnow().strftime("%d/%m/%y")
        for result in results:
            name = result["name"]
            category = result.get("category", None)
            if category is None:
                category = self.vectorizer.select_category(name)

            tags = self.vectorizer.extract_tags(name, category)
            if tags == []:
                continue

            price = float(result["price"])
            is_promo = result.get("promo", None)
            is_afiliate = result.get("is_afiliate", None)
            url = result.get("url", "")
            new_price = Price(date=today, price=price, is_promo=is_promo, is_afiliate=is_afiliate, url=url)
            new_product = False

            product_dict = self.database.find_product(tags)
            if product_dict is None:
                new_product = True
                self.database.new_product(Product(raw_name=name, category=category, tags=tags, price=price, history=[new_price.__dict__]).__dict__)

            # New product
            product_dict = self.database.find_product(tags)
            product_obj = Product(**product_dict)
            old_price = product_obj.verify_in_history(new_price)
            if not old_price:
                self.database.update_product_history(tags, price, new_price)
            else:
                logging.warning("Nao eh preco novo") # Mas alguem pode ainda nao ter recebido essa oferta

            all_wishes = self.database.find_all_wishes(tags)
            all_chats_id = {chat_id for wish_list in all_wishes for chat_id in wish_list["users"]}

            avarage_price = product_obj.avarage()
            sent_idx = product_obj.verify_get_in_sents(new_price)
            if (new_product or
                new_price.price < avarage_price * (1-MINIMUN_DISCOUNT) or
                (None not in (sent_idx, all_wishes) and set(product_obj.sents[sent_idx]["users"]) <= all_chats_id)):

                if sent_idx is None:
                    current_sent = new_price
                    current_sent.users = []
                else:
                    current_sent = product_obj.get_sents()[sent_idx]

                for wish_list in all_wishes:
                    for chat_id in wish_list["users"]:
                        chat_id
                        if chat_id not in current_sent.users:
                            # Send to user and to sents list
                            current_sent.users.append(chat_id)
                            await self.send_to_user(chat_id, result)

                self.database.update_product_sents(tags, current_sent, sent_idx)

            else:
                logging.warning(f"Nao eh oferta boa (Minimo: {MINIMUN_DISCOUNT * 100}%)")

    def verify_get_in_sents(self, new_price: Price | dict):
        if type(new_price) is dict:
            new_price = Price(**new_price)

        return new_price in self.get

    async def send_to_user(self, chat_id: int, result: dict):

        await self.telegram_bot.send_message(chat_id, str(result))

    def get_urls(self):
        return self.database.get_links