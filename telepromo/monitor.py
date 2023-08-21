import importlib
import logging
import time
import traceback

from models import Product, Price
from graphs import Metrics
from database import Database
from vectorizers import Vectorizers
from telegram_bot import TelegramBot

MINIMUN_DISCOUNT = 0.05

class Monitoring (object):
    """
    Class to monitoring sites in url
    """
    database: Database
    vectorizer: Vectorizers
    telegram_bot: TelegramBot

    def __init__ (self, **kwargs):
        self.retry = kwargs.get("retrys")
        self.database = kwargs.get("database")
        self.vectorizer = kwargs.get("vectorizer")
        self.telegram_bot = kwargs.get("telegram_bot")

    async def prices_from_url (self, urls: list[dict]) -> list:
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

            try:
                bot_module = importlib.import_module(f"bots.{bot_name}")
                bot_class = getattr(bot_module, bot_name)
                bot_instance = bot_class()
                results = await bot_instance.run(link=link)
                logging.warning(f"{bot_name}: {len(results)} found products.")
                all_results += results

            except Exception as exc:
                logging.error(f"bot {bot_name} error: {exc}")
                logging.error(traceback.format_exc())
                continue

        return all_results

    async def verify_save_prices (self, results: dict, category: str):
        today = int(time.time())

        new_metric = Metrics(category)

        for result in results:
            name = result["name"].replace("\n", " ")

            # Get only relevant names from raw name
            tags = self.vectorizer.extract_tags(name, category)
            if tags == []:
                continue

            price = result["price"]

            product_obj = Product(
                raw_name=name, category=category, tags=tags,
                price=price, history=[]
            )

            old_product, product_dict = self.database.find_product(product_obj)
            if not old_product:
                new_metric.update_values(news=1)

            # New product
            product_obj = Product(**product_dict)

            # Create New Price or Find
            old_price = result["old_price"]

            if old_price is None:
                old_price = price

            if not isinstance(price, (float, int)) or not isinstance(old_price, (float, int)):
                logging.error("Mismatch price error (not valid float), skipping...")
                logging.error(traceback.format_exc())

            is_promo = result.get("promo", None)
            if is_promo is None and (old_price < price):
                is_promo = True

            is_affiliate = result.get("is_affiliate", None)
            url = result.get("url", "")

            new_price = Price(
                date=today, price=price, old_price=old_price, is_promo=is_promo,
                is_affiliate=is_affiliate, url=url
            )

            is_new_price, price_obj, price_index = self.database.verify_or_add_price(
                tags, new_price, product_obj
            )

            if is_new_price:
                new_metric.update_values(offers=1)

            all_wishes = self.database.find_all_wishes(tags)

            for wish in all_wishes:
                users_wish = wish["users"]

                if len(users_wish) == 0:
                    continue

                list_user_tags = wish["tags"]
                set_user_tags = set(list_user_tags)

                needed = 0.5    # Need at least half of tags to send
                tam_user_tags = len(list_user_tags)

                qtd_equals = len(set_user_tags.intersection(tags))

                prct_equal = qtd_equals / tam_user_tags

                if prct_equal < needed:
                    continue

                for user_id in users_wish:

                    # Caso onde ja foi enviado aquela oferta para o usuario
                    if user_id in price_obj.users_sent and price_obj.users_sent[user_id] == 1:
                        continue

                    user_price = users_wish[user_id]

                    if price > user_price * 1.03 and user_price != 0:
                        self.database.add_new_user_in_price_sent(
                            product_obj._id, price_index, user_id, 0
                        )
                        continue

                    await self.send_to_user(user_id, result)

                    self.database.add_new_user_in_price_sent(
                        product_obj._id, price_index, user_id, 1
                    )
                    new_metric.update_values(sent=1)

        return new_metric

    def verify_get_in_sents (self, new_price: Price | dict):
        if type(new_price) is dict:
            new_price = Price(**new_price)

        return new_price in self.get

    async def send_to_user (self, chat_id: int, result: dict):

        await self.telegram_bot.send_message(chat_id, str(result))
