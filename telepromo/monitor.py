import importlib
import logging
import datetime
import json

class Monitoring(object):
    """
    Class to monitoring sites in url
    """
    database: object
    vectorizer: object

    def __init__(self, **kwargs):
        self.retry = kwargs.get("retrys")
        self.database = kwargs.get("database")
        self.vectorizer = kwargs.get("vectorizer")

    def prices_from_url(self, urls: list[dict]) -> list:
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
            results = bot_instance.run(link=link)
            all_results += results

        return all_results

    def verify_save_prices(self, results: dict):
        for result in results:
            name = result['name']
            tags = self.vectorizer.extract_tags(name)
            category = result.get('category', None)
            if category is None:
                category = self.vectorizer.select_category(name)
            
            price = result['price']
            is_promo = result.get('promo', None)

            product_obj = self.database.find_product(category, tags)
            if product_obj is None:
                self.database.new_product(category, {
                    'raw_name': name,
                    'tags': tags,
                    'price': price,
                    'sents': []
                })

            # New product
            product_obj = self.database.find_product(category, tags)
            all_sents = product_obj['sents']
            today = datetime.datetime.utcnow()
            new_sent = None
            if (is_promo or (all_sents == []) or all_sents[-1]['price'] > price):# or (all_sents[-1]['date'] - today == 1)):
                new_sent = {
                    'date': str(today),
                    'price': price,
                    'is_promo': is_promo,
                    'url': ''
                }
            self.database.update_product(category, tags, price, new_sent)

            all_wishes = self.database.find_all_wishes(tags)
            for wish_list in all_wishes:
                for name in wish_list['users']:
                    logging.warning(f"Usuario {name}, olha essa oferta de '{' '.join(tags)}'!\n{json.dumps(new_sent, indent=4)}")

    def get_urls(self):
        return self.database.get_links