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

    async def verify_save_prices(self, results: dict):
        today = datetime.datetime.utcnow().strftime("%d/%m/%y")
        for result in results:
            name = result['name']
            tags = self.vectorizer.extract_tags(name)
            if tags == []:
                continue

            category = result.get('category', None)
            if category is None:
                category = self.vectorizer.select_category(name)
            
            price = float(result['price'])
            is_promo = result.get('promo', None)
            is_afiliate = result.get('is_afiliate', None)
            new_price = Price(date=today, price=price, is_promo=is_promo, is_afiliate=is_afiliate, url="")
            new_product = False

            product_dict = self.database.find_product(category, tags)
            if product_dict is None:
                new_product = True
                self.database.new_product(category, Product(raw_name=name, tags=tags, price=price, history=[new_price.__dict__]).__dict__)

            # New product
            product_dict = self.database.find_product(category, tags)
            all_wishes = None
            product_obj = Product(**product_dict)
            old_price = product_obj.verify_in_history(new_price)
            # Verify if the price from the THIS site exists
            if not old_price:
                #self.database.update_product(category, tags, price, new_price)

                # Verify if its a new product or the discount is the minimun
                #logging.warning(f"product avg {product_obj.avarage()}")
                #logging.warning(f"new price {new_price.price}")
                #logging.warning(f"discount {MINIMUN_DISCOUNT}")
                if new_product or new_price.price * MINIMUN_DISCOUNT < product_obj.avarage():
                    all_wishes = self.database.find_all_wishes(tags)
                    new_sent = new_price
                
                    if all_wishes is not None:
                        for wish_list in all_wishes:
                            for chat_id in wish_list['users']:
                                await self.send_to_user(chat_id, result)
                    else:
                        logging.warning("Nenhum alerta para esse produto")
                else:
                    logging.warning(f"Nao eh oferta boa (Minimo: {MINIMUN_DISCOUNT * 100}%)")
            else:
                logging.warning("Nao eh oferta nova")

    async def send_to_user(self, chat_id: int, result: dict):
        
        await self.telegram_bot.send_message(chat_id, str(result))


    def get_urls(self):
        return self.database.get_links