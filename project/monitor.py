import importlib
import logging
import time
import traceback

from project.database import Database
from project.graphs import Metrics
from project.models import Price, Product, FormatPromoMessage
from project.telegram_bot import TelegramBot
from project.vectorizers import Vectorizers
from project.metrics_collector import MetricsCollector

MINIMUN_DISCOUNT = 0.05

class Monitoring (object):
    """
    Class to monitoring sites in url
    """
    database: Database
    vectorizer: Vectorizers
    telegram_bot: TelegramBot
    metrics_collector: MetricsCollector

    def __init__ (self, **kwargs):
        self.retry = kwargs.get("retrys")
        self.database = kwargs.get("database")
        self.vectorizer = kwargs.get("vectorizer")
        self.telegram_bot = kwargs.get("telegram_bot")
        self.metrics_collector = kwargs.get("metrics_collector")

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
                bot_module = importlib.import_module(f"project.bots.{bot_name}")
                bot_class = getattr(bot_module, bot_name)
                bot_instance = bot_class()
                results = await bot_instance.run(link=link, brand=bot_name)
                logging.warning(f"{bot_name}: {len(results)} found products.")
                all_results += results
                self.metrics_collector.consume_site(bot_name, "Sucess", len(results))

            except Exception as exc:
                self.metrics_collector.handle_error("load_bot_and_results")
                logging.error(f"bot {bot_name} error: {exc}")
                logging.error(traceback.format_exc())

                continue

        return all_results

    async def verify_save_prices (self, results: dict, category: str):
        today = int(time.time())

        new_metric = Metrics(category)

        for result in results:
            try:
                name = result["name"].replace("\n", " ")

                # Get only relevant names from raw name
                tags = self.vectorizer.extract_tags(name, category)
                if tags == []:
                    continue

                price = result["price"]
                old_price = result["old_price"]

                product_obj = Product(
                    raw_name=name, category=category, tags=tags,
                    price=price, history=[]
                )

                old_product, product_dict = self.database.find_product(product_obj)
                if not old_product:
                    self.metrics_collector.handle_product("new_product")

                # New product
                product_obj = Product(**product_dict)

                if not isinstance(price, (float, int)) or not isinstance(old_price, (float, int)):
                    self.metrics_collector.handle_error("parse_price_to_float")
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

                avarage = price
                if old_product:
                    avarage = product_obj.avarage()

                if is_new_price:
                    self.metrics_collector.handle_product("new_price")

                all_wishes = self.database.find_all_wishes(tags)

                for wish in all_wishes:
                    users_wish = wish["users"]

                    if len(users_wish) == 0:
                        continue

                    list_user_tags = wish["tags"]
                    set_user_tags = set(list_user_tags)

                    needed = 0.5                    # Need at least half of tags to send
                    if len(list_user_tags) == 2:    # Special case, only two tags
                        needed = 1.0

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

                        beautiful_msg = FormatPromoMessage.parse_msg(result, avarage, prct_equal)
                        await self.send_to_user(user_id, beautiful_msg)

                        self.database.add_new_user_in_price_sent(
                            product_obj._id, price_index, user_id, 1
                        )
                        self.metrics_collector.handle_user_response()


            except Exception:
                self.metrics_collector.handle_error("get_results")
                logging.error(traceback.print_exc())

        return new_metric

    def verify_get_in_sents (self, new_price: Price | dict):
        if type(new_price) is dict:
            new_price = Price(**new_price)

        return new_price in self.get

    async def send_to_user (self, chat_id: int, offer_message: str):
        await self.telegram_bot.send_message(chat_id, offer_message)
