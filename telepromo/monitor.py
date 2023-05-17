import importlib
import logging
import datetime
import json
from typing import List

from models import Product, Price
from database import Database
from vectorizers import Vectorizers
from telegram_bot import TelegramBot

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

    async def prices_from_url(self, urls: List[dict]) -> list:
        """
        Get a URL and return the dict with prices
        """
        all_results = []
        for url in urls:
            link = url['link']
            bot_name = url['name']
            if link == "":
                logging.warn(f"{bot_name} não tem link, skipando...")
                continue

            bot_module = importlib.import_module(f"bots.{bot_name}")
            bot_class = getattr(bot_module, bot_name)
            bot_instance = bot_class()
            results = await bot_instance.run(link=link)
            all_results += results

        return all_results

    def verify_save_prices(self, results: dict):
        for result in results:
            name = result['name']
            tags = self.vectorizer.extract_tags(name)
            if tags == []: # Produtos irrelevantes
                continue

            category = result.get('category', None)
            if category is None:
                category = self.vectorizer.select_category(name)
            
            price = result['price']
            is_promo = result.get('promo', None)
            is_afiliate = result.get('is_afiliate', None)
            new_price = Price(date=today.strftime("%d%m%y"), price=price, is_promo=is_promo, is_afiliate=is_afiliate, url="").__dict__

            product_obj = self.database.find_product(category, tags)
            if product_obj is None:
                self.database.new_product(category, Product(raw_name=name, tags=tags, price=price, history=[new_price]).__dict__)

            # New product
            product_obj = self.database.find_product(category, tags)
            all_sents = product_obj['sents']
            today = datetime.datetime.utcnow().strftime("%d/%m/%y")
            all_wishes = None
            if (is_promo or (all_sents == []) or product_obj.avarage > price):# or (all_sents[-1]['date'] - today == 1)):

                self.database.update_product(category, tags, price, new_price)
                all_wishes = self.database.find_all_wishes(tags)
            
                if all_wishes is not None:
                    for wish_list in all_wishes:
                        for name in wish_list['users']:
                            logging.warning(f"Usuario {name}, olha essa oferta de '{' '.join(tags)}'!\n{json.dumps(new_sent, indent=4)}")
                else:
                    logging.warning("Ninguem quer")
            else:
                logging.warning("N eh oferta boa/nova")

    def get_urls(self):
        return self.database.get_links