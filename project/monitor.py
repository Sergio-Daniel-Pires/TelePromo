import asyncio
import json
import logging
import time
import traceback
from typing import Any

from redis import Redis

from project import config
from project.bots import base
from project.database import Database
from project.metrics_collector import MetricsCollector
from project.models import FormatPromoMessage, Price, Product, Wish, WishGroup
from project.utils import brand_to_bot
from project.vectorizers import Vectorizers


class Monitoring :
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

        self.redis_client.set("stop_signal", 0)

    def enqueue_bot_pages (self, urls: list[dict], category: str) -> list[asyncio.Future]:
        """
        Get a URL and return the dict with prices
        """
        ready_to_run = []
        time_now = int(time.time())

        for idx, page_obj in enumerate(urls):
            link = page_obj["link"]
            api_link = page_obj.get("api_link", None)
            brand = page_obj["name"]
            status = page_obj["status"]
            last = page_obj.get("last", None)
            repeat = page_obj.get("repeat", None)

            if link == "":
                logging.debug(f"{brand} não tem link, skipando...")
                continue

            if status != "NEW" and last + repeat > time_now:
                logging.debug(f"{brand} ainda não passou tempo suficiente...")
                continue

            if repeat == 0:
                logging.error(f"{brand}: Error repeat 0")

            if repeat < self.shortest_bot_time and repeat != 0:
                self.shortest_bot_time = repeat

            try:
                bot_instance = brand_to_bot[brand](
                    link=link, index=idx, category=category,
                    metadata=page_obj, api_link=api_link
                )
                ready_to_run.append(bot_instance)

            except Exception as exc:
                self.metrics_collector.handle_error("load_bot_and_results")
                logging.error(f"bot {brand} error: {exc}")
                logging.error(traceback.format_exc())

        return ready_to_run

    async def verf_price_is_good (
        self, brand: str, offer_name: str, category: str, price: float
    ) -> tuple[bool, Product, int]:
        """
        Verify if its is a new price, product as object and index in fast acess dict

        :param brand: Bot name
        :param offer_name: Offer name in site
        :param category: like eletronics, clothes etc
        :param price: float price
        """
        # Verificações diarias pra economizar em querys do MongoDB
        if category not in self.today_offers:
            self.today_offers[category] = {}

        if brand not in self.today_offers[category]:
            self.today_offers[category][brand] = []

        bot_offers = self.today_offers[category][brand]

        # Get only relevant names from raw name
        tags, adjectives = await self.vectorizer.extract_tags(offer_name, category)

        if len(tags) == 0:
            return None, None, None

        product_obj = Product(
            raw_name=offer_name, category=category, tags=tags, adjectives=adjectives,
            price=price, history=[]
        )
        new_product = False

        if product_obj not in bot_offers:
            new_product, product_dict = self.database.find_or_insert_product(product_obj)

            if new_product:
                self.metrics_collector.handle_site_results(brand, "new_product")

            # New product
            product_obj = Product(**product_dict)
            bot_offers.append(product_obj)
            index = len(bot_offers) - 1

        else:
            index = bot_offers.index(product_obj)
            product_obj = bot_offers[index]

        return new_product, product_obj, index

    async def send_products_to_wish (
        self, all_wishes: list[WishGroup], product_obj: Product,
        product_idx: int, price_obj: Price, price_idx: int
    ):
        brand = price_obj.brand

        for wish in all_wishes:
            users_wish = wish["users"]

            if len(users_wish) == 0:
                continue

            user_tags = set(wish["tags"])

            needed = 0.75              # Need at least half of tags to send
            if len(user_tags) == 2:    # Special case, only two tags
                needed = 1.0

            tam_user_tags = len(user_tags)

            qtd_equals = len(user_tags.intersection(product_obj.tags))

            prct_equal = qtd_equals / tam_user_tags

            if prct_equal < needed:
                continue

            for user_id in users_wish:
                # Case when msg was sent for user
                if (
                    user_id in price_obj.users_sent and price_obj.users_sent[user_id] == 1
                ):
                    continue

                user_wish = Wish(**users_wish[user_id])

                if (
                    (product_obj.price > user_wish.price * 1.03 and user_wish.price != 0) or
                    len(set(user_wish.blacklist).intersection(set(product_obj.tags))) > 0
                ):
                    self.update_sents(0, product_obj, price_idx, product_idx, brand, user_id)
                    continue

                # Add to background queue
                beautiful_msg = FormatPromoMessage.parse_msg(price_obj, product_obj, prct_equal)
                self.redis_client.lpush(
                    "msgs_to_send", json.dumps({ "chat_id": user_id, "message": beautiful_msg })
                )

                self.update_sents(0, product_obj, price_idx, product_idx, brand, user_id)

    def update_sents (
        self, has_sent: bool, product_obj: Product, price_idx, product_idx, brand, user_id
    ):
        self.database.add_new_user_in_price_sent(product_obj._id, price_idx, user_id, has_sent)

        # Faster way to acess sent history dict
        if product_obj.category in self.today_offers:
            history = self.today_offers[product_obj.category][brand][product_idx].history
            history[price_idx].users_sent[user_id] = has_sent

        if has_sent:
            self.metrics_collector.handle_user_response()

    async def handle_bot_results (self, results: list[base.BotRunner]):
        for bot_result in results:
            # update bot results
            is_ok = "OK" if bot_result.is_ok else "ERROR"
            self.database.update_link(
                bot_result.category, bot_result.index, is_ok, bot_result.metadata
            )
            logging.warning(f"Starting {bot_result.brand}#{bot_result.index}")

            for offer in bot_result.results:
                await self.send_offer_to_user(offer)

            logging.warning(f"Finished {bot_result.brand}#{bot_result.index}")

    async def send_offer_to_user (self, offer: dict[str, Any]):
        brand = offer["brand"]
        category = offer["category"]
        price = offer["price"]
        old_price = offer["old_price"]
        name = offer["name"].replace("\n", " ")

        try:
            product_verf_result = await self.verf_price_is_good(brand, name, category, price)
            _, product_obj, product_index = product_verf_result

            if product_obj is None:
                return None

            tags = product_obj.tags

            if not isinstance(price, (float, int)) or not isinstance(old_price, (float, int)):
                self.metrics_collector.handle_error("parse_price_to_float")
                logging.error("Mismatch price error (not valid float), skipping...")
                logging.error(traceback.format_exc())

            is_promo = offer.get("promo", None)
            if is_promo is None and (old_price > price):
                is_promo = True

            new_price = Price(
                date=int(time.time() * 1000), price=price, old_price=old_price,
                is_promo=is_promo, is_affiliate=offer.get("is_affiliate", None),
                url=offer["url"], brand=brand, img=offer["img"], extras=offer.get("extras", {})
            )

            is_new_price, price_obj, price_index = self.database.verify_or_add_price(
                tags, new_price, product_obj
            )

            if is_new_price:
                self.today_offers[category][brand][product_index].history.append(price_obj)
                self.metrics_collector.handle_site_results(brand, "new_price")

            # Just to try msg are sent
            if brand not in self.tested_brands:
                beautiful_msg = FormatPromoMessage.parse_msg(new_price, product_obj, 1)

                self.redis_client.lpush(
                    "msgs_to_send", json.dumps(
                        { "chat_id": config.BOT_OWNER_CHAT_ID, "message": beautiful_msg }
                    )
                )
                self.tested_brands.add(brand)

            all_wishes = self.database.find_all_wishes(tags)

            await self.send_products_to_wish(
                all_wishes, product_obj, product_index,
                price_obj, price_index
            )

        except Exception:
            self.metrics_collector.handle_site_results(brand, "error")
            self.metrics_collector.handle_error("get_results")
            logging.error(traceback.print_exc())

    async def continuous_verify_price (self):
        links_cursor = self.database.get_links()

        logging.warning("Verifying bots that need to run...")
        ready_pages = []

        for link_obj in links_cursor:
            url_list = link_obj["links"]
            category = link_obj["category"]

            # Get raw results from web scraping
            ready_pages += self.enqueue_bot_pages(url_list, category)

        logging.warning("Finished bots verification...")

        logging.warning("Started...")
        await base.BotBase(ready_pages, True).run(self.handle_bot_results)

        logging.warning("Parsed all products found")
        logging.warning("Finished pipeline")

        return True
