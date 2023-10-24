import asyncio
import json
import logging
import time
import traceback

from redis import Redis

from project.bots import base
from project.database import Database
from project.metrics_collector import MetricsCollector
from project.models import FormatPromoMessage, Price, Product, Wished
from project.utils import name_to_object
from project.vectorizers import Vectorizers
from typing import Any


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

    tested_categories: set  # Only to try all chats
    tested_brands: set  # Only to try all chats

    today_offers: dict[str, dict[str, list[Product]]]

    def __init__ (self, **kwargs):
        self.retry = kwargs.get("retrys")
        self.database = kwargs.get("database")
        self.vectorizer = kwargs.get("vectorizer")
        self.metrics_collector = kwargs.get("metrics_collector")
        self.redis_client = kwargs.get("redis_client")

        self.last_execution_time = 0
        self.shortest_bot_time = 60 * 15

        self.tested_categories = set()
        self.tested_brands = set()

        self.today_offers = {}

        self.redis_client.set(
            "stop_signal", 0
        )

    def verify_ready_pages (self, urls: list[dict], category: str) -> list[asyncio.Future]:
        """
        Get a URL and return the dict with prices
        """
        ready_to_run = []
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

            try:
                bot_instance = name_to_object[bot_name](
                    link=link, index=idx, category=category, metadata=url
                )
                ready_to_run.append(bot_instance)

            except Exception as exc:
                self.metrics_collector.handle_error("load_bot_and_results")
                logging.error(f"bot {bot_name} error: {exc}")
                logging.error(traceback.format_exc())

        return ready_to_run

    async def product_verification (
        self, bot_name: str, offer_name: str, category: str, price: float
    ) -> tuple[bool, Product, int]:
        """
        Verify if its is a new price, product as object and index in fast acess dict

        :param bot_name: Bot name
        :param offer_name: Offer name in site
        :param category: like eletronics, clothes etc
        :param price: float price
        """
        # Verificações diarias pra economizar em querys do MongoDB
        if category not in self.today_offers:
            self.today_offers[category] = {}
        if bot_name not in self.today_offers[category]:
            self.today_offers[category][bot_name] = []

        bot_offers = self.today_offers[category][bot_name]

        # Get only relevant names from raw name
        tags, adjectives = await self.vectorizer.extract_tags(offer_name, category)
        if tags == []:
            return None, None

        product_obj = Product(
            raw_name=offer_name, category=category, tags=tags, adjectives=adjectives,
            price=price, history=[]
        )
        new_product = False

        if product_obj not in bot_offers:
            # timer.next("Find product")
            new_product, product_dict = self.database.find_product(product_obj)

            if new_product:
                self.metrics_collector.handle_site_results(bot_name, "new_product")

            # New product
            product_obj = Product(**product_dict)
            bot_offers.append(product_obj)
            index = len(bot_offers) - 1

        else:
            index = bot_offers.index(product_obj)
            product_obj = bot_offers[index]

        return new_product, product_obj, index

    async def handle_users_wishes (
        self, all_wishes: list[Wished], product_obj: Product, product_idx: int, price_obj: Price,
        price_idx: int, offer: dict[str, Any], avg: float
    ):
        bot_name = offer["bot"]
        category = offer["category"]

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

            qtd_equals = len(set_user_tags.intersection(product_obj.tags))

            prct_equal = qtd_equals / tam_user_tags

            if prct_equal < needed:
                continue

            for user_id in users_wish:

                # Caso onde ja foi enviado aquela oferta para o usuario
                if (
                    user_id in price_obj.users_sent and
                    price_obj.users_sent[user_id] == 1
                ):
                    continue

                user_price = users_wish[user_id]

                if product_obj.price > user_price * 1.03 and user_price != 0:
                    self.database.add_new_user_in_price_sent(
                        product_obj._id, price_idx, user_id, 0
                    )
                    self.today_offers[category][bot_name][product_idx].history[price_idx].users_sent[user_id] = 0
                    continue

                beautiful_msg = FormatPromoMessage.parse_msg(
                    offer, avg, prct_equal, bot_name
                )
                # Add to background queue
                self.redis_client.lpush(
                    "msgs_to_send", json.dumps(
                        { "chat_id": user_id, "message": beautiful_msg }
                    )
                )

                self.database.add_new_user_in_price_sent(
                    product_obj._id, price_idx, user_id, 1
                )
                # Faster acess dict
                self.today_offers[category][bot_name][product_idx].history[price_idx].users_sent[user_id] = 1
                self.metrics_collector.handle_user_response()

    async def verify_save_prices (self, results: list[base.BotRunner]):
        today = int(time.time())

        # last_bot = None
        for bot_result in results:
            # update bot results
            is_ok = "OK" if bot_result.is_ok else "ERROR"
            self.database.update_link(
                bot_result.category, bot_result.index, is_ok, bot_result.metadata
            )
            logging.warning(f"Starting {bot_result.brand}#{bot_result.index}")

            for offer in bot_result.results:
                bot_name = offer["bot"]
                category = offer["category"]
                price = offer["price"]
                old_price = offer["old_price"]
                name = offer["name"].replace("\n", " ")

                try:
                    product_verf_result = await self.product_verification(
                        bot_name, name, category, price
                    )
                    is_new_product, product_obj, product_index = product_verf_result

                    if product_obj is None:
                        continue

                    tags = product_obj.tags

                    if not isinstance(price, (float, int)) or not isinstance(old_price, (float, int)):
                        self.metrics_collector.handle_error("parse_price_to_float")
                        logging.error("Mismatch price error (not valid float), skipping...")
                        logging.error(traceback.format_exc())

                    is_promo = offer.get("promo", None)
                    if is_promo is None and (old_price > price):
                        is_promo = True

                    new_price = Price(
                        date=today, price=price, old_price=old_price,
                        is_promo=is_promo, is_affiliate=offer.get("is_affiliate", None),
                        url=offer["url"], extras=offer.get("extras", {})
                    )

                    is_new_price, price_obj, price_index = self.database.verify_or_add_price(
                        tags, new_price, product_obj
                    )

                    if is_new_price:
                        self.today_offers[category][bot_name][product_index].history.append(price_obj)
                        self.metrics_collector.handle_site_results(bot_name, "new_price")

                    avarage = price
                    if not is_new_product:
                        avarage = product_obj.avarage()

                    # Just to try msg are sent
                    if category not in self.tested_categories or bot_name not in self.tested_brands:
                        beautiful_msg = FormatPromoMessage.parse_msg(offer, avarage, 1, bot_name)

                        self.redis_client.lpush(
                            "msgs_to_send", json.dumps(
                                { "chat_id": "783468028", "message": beautiful_msg }
                            )
                        )
                        self.tested_categories.add(category)
                        self.tested_brands.add(bot_name)

                    all_wishes = self.database.find_all_wishes(tags)

                    await self.handle_users_wishes(
                        all_wishes, product_obj, product_index, price_obj, price_index,
                        offer, avarage
                    )

                except Exception:
                    self.metrics_collector.handle_site_results(bot_name, "error")
                    self.metrics_collector.handle_error("get_results")
                    logging.error(traceback.print_exc())

            logging.warning(f"Finished {bot_result.brand}#{bot_result.index}")

    async def continuous_verify_price (self):
        links_cursor = self.database.get_links()

        logging.warning("Verifying bots that need to run...")
        ready_pages = []

        for link_obj in links_cursor:

            url_list = link_obj["links"]
            category = link_obj["category"]

            # Get raw results from web scraping
            ready_pages += self.verify_ready_pages(url_list, category)
        logging.warning("Finished bots verification...")

        logging.warning("Started...")
        await base.BotBase(ready_pages, True).run(self.verify_save_prices)

        logging.warning("Parsed all products found")
        logging.warning("Finished pipeline")

        return True
