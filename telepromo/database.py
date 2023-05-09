from pymongo import MongoClient

from bots import LINKS
from models import Wished

class Database(object):
    """
    A class to manage connection with python and mongoDB
    """

    client = MongoClient
    database = dict

    def __init__(self):
        self.client = MongoClient("mongodb", 27017)
        self.database = self.client['telepromo']

        # Initialize collections
        if not 'links' in self.database.list_collection_names():
            self.database['links'].insert_many(LINKS)

    # Product Funcs
    def get_links(self):
        links = self.database['links'].find({})
        return links

    def find_product(self, category: str, tags: list):
        product = self.database[category].find_one({"tags": {"$all": tags}})
        return product
    
    def new_product(self, category: str, product: dict):
        self.database[category].insert_one(product)

    def update_product(self, category: str, tags: list, new_price: float, new_sent: dict = None):
        self.database[category].update_one({"tags": {"$all": tags}}, {"$set": {'price': new_price}})
        if new_sent is not None:
            self.database[category].update_one({"tags": {"$all": tags}}, {"$push": {"sents": new_sent}})

    # Wish Funcs
    def new_wish(self, tags: list, category: str, user: str, links: list = []):        
        wish_obj = self.find_wish(tags)
        if wish_obj is None:
            self.database['wishes'].insert_one(
                Wished(tags, category, links=links).__dict__
            )
        wish_obj = self.find_wish(tags)
        if user in wish_obj['users']:
            return False
        
        wish_obj = self.database['wishes'].update_one({"tags": {"$all": tags}}, {"$push": {"users": user}})
        return True

    def find_wish(self, tags: list):
        return self.database['wishes'].find_one({"tags": {"$all": tags}})
    
    def find_all_wishes(self, tags: list):
        return self.database['wishes'].find({"tags": {"$in": tags}})