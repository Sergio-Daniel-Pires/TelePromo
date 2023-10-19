import asyncio
import importlib
import json
import logging
import time
import traceback
import threading

from redis import Redis
from telegram.ext import ContextTypes

from project.database import Database
from project.metrics_collector import MetricsCollector
from project.models import FormatPromoMessage, Price, Product
from project.vectorizers import Vectorizers


class Monitoring (object):
    """
    Class to monitoring sites in url
    """
    database: Database
    vectorizer: Vectorizers
    metrics_collector: MetricsCollector
    redis_client: Redis

    last_execution_time: int
    shortest_bot_time: int

    first_sent: bool  # Only to try sent_msg

    def __init__ (self, **kwargs):
        self.retry = kwargs.get("retrys")
        self.database = kwargs.get("database")
        self.vectorizer = kwargs.get("vectorizer")
        self.metrics_collector = kwargs.get("metrics_collector")
        self.redis_client = kwargs.get("redis_client")

        self.last_execution_time = 0
        self.shortest_bot_time = 60 * 15

        self.first_sent = False

        self.redis_client.set(
            "stop_signal", 0
        )

    async def prices_from_url (self, urls: list[dict], category: str) -> list:
        """
        Get a URL and return the dict with prices
        """
        all_results = []
        time_now = int(time.time())

        for idx, url in enumerate(urls):
            link = url["link"]
            bot_name = url["name"]
            status = url["status"]
            last = url.get("last", None)
            repeat = url.get("repeat", None)

            if link == "":
                logging.debug(f"{bot_name} não tem link, skipando...")
                continue

            if status != "NEW" and last + repeat > time_now:
                logging.debug(f"{bot_name} ainda não passou tempo suficiente...")
                continue

            if repeat == 0:
                logging.error(f"{bot_name}: Error repeat 0")

            if repeat < self.shortest_bot_time and repeat != 0:
                self.shortest_bot_time = repeat

            logging.warning(f"Trying to run {bot_name}...")

            try:
                bot_module = importlib.import_module(f"project.bots.{bot_name}")
                bot_class = getattr(bot_module, bot_name)
                bot_instance = bot_class()
                results = await bot_instance.run(link=link, brand=bot_name)
                logging.warning(f"{bot_name}: {len(results)} found products.")
                all_results += results
                status = "OK"

            except Exception as exc:
                self.metrics_collector.handle_error("load_bot_and_results")
                logging.error(f"bot {bot_name} error: {exc}")
                logging.error(traceback.format_exc())
                status = "ERROR"

            self.database.update_link(category, idx, status, url)

        return all_results

    async def verify_save_prices (
        self, results: dict, category: str
    ):
        today = int(time.time())

        # last_bot = None
        for result in results:
            bot_name = result["bot"]
            # if last_bot is None or last_bot != bot_name:
            #     last_bot = bot_name
            #     self.first_sent = False

            try:
                name = result["name"].replace("\n", " ")

                # Get only relevant names from raw name
                tags, adjectives = self.vectorizer.extract_tags(name, category)
                if tags == []:
                    continue

                price = result["price"]
                old_price = result["old_price"]

                product_obj = Product(
                    raw_name=name, category=category, tags=tags, adjectives=adjectives,
                    price=price, history=[]
                )

                new_product, product_dict = self.database.find_product(product_obj)
                if new_product:
                    self.metrics_collector.handle_site_results(bot_name, "new_product")

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
                extras = result.get("extras", {})

                new_price = Price(
                    date=today, price=price, old_price=old_price, is_promo=is_promo,
                    is_affiliate=is_affiliate, url=url, extras=extras
                )

                is_new_price, price_obj, price_index = self.database.verify_or_add_price(
                    tags, new_price, product_obj
                )

                avarage = price
                if not new_product:
                    avarage = product_obj.avarage()

                if is_new_price:
                    self.metrics_collector.handle_site_results(bot_name, "new_price")

                # Just to try msg are sent
                if not self.first_sent:
                    beautiful_msg = FormatPromoMessage.parse_msg(result, avarage, 1, bot_name)
                    self.redis_client.lpush(
                        "msgs_to_send", json.dumps(
                            { "chat_id": "783468028", "message": beautiful_msg }
                        )
                    )
                    self.first_sent = True

                all_wishes = self.database.find_all_wishes(tags)

                for wish in all_wishes:
                    users_wish = wish["users"]

                    if len(users_wish) == 0:
                        continue

                    list_user_tags = wish["tags"]
                    set_user_tags = set(list_user_tags)

                    needed = 0.75                   # Need at least half of tags to send
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

                        beautiful_msg = FormatPromoMessage.parse_msg(
                            result, avarage, prct_equal, bot_name
                        )
                        # Add to background queue
                        self.redis_client.lpush(
                            "msgs_to_send", json.dumps(
                                { "chat_id": user_id, "message": beautiful_msg }
                            )
                        )

                        self.database.add_new_user_in_price_sent(
                            product_obj._id, price_index, user_id, 1
                        )
                        self.metrics_collector.handle_user_response()

            except Exception:
                self.metrics_collector.handle_site_results(bot_name, "error")
                self.metrics_collector.handle_error("get_results")
                logging.error(traceback.print_exc())

    def verify_get_in_sents (self, new_price: Price | dict):
        if type(new_price) is dict:
            new_price = Price(**new_price)

        return new_price in self.get

    async def process_link (self, link_obj):
        try:
            url_list = link_obj["links"]
            category = link_obj["category"]

            # Get raw results from web scraping
            results = await self.prices_from_url(url_list, category)

            await self.verify_save_prices(results, category)
        except Exception as exc:
            logging.error(exc)

    async def continuous_verify_price (self):
        links_cursor = self.database.get_links()

        logging.warning("Starting requests...")
        tasks = [ self.process_link(link_obj) for link_obj in links_cursor ]
        await asyncio.gather(*tasks)

        logging.warning("Verified all urls!")
        return True
