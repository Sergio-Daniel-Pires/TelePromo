from pymongo import MongoClient

from bots.base import LINKS
from models import Wished, User, Price

import logging

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

    def find_product(self, tags: list):
        product = self.database['products'].find_one({"tags": {"$all": tags}})
        return product
    
    def new_product(self, product: dict):
        self.database['products'].insert_one(product)

    def update_product_history(self, tags: list, price: float, new_price: dict | Price = None):
        self.database['products'].update_one({"tags": {"$all": tags}}, {"$set": {'price': price}})
        if new_price is not None:
            if type(new_price) is Price:
                new_price = new_price.__dict__

            self.database['products'].update_one({"tags": {"$all": tags}}, {"$push": {"history": new_price}})

    def update_product_sents(self, tags: list, new_sent: Price | dict, index: bool):
        if type(new_sent) is Price:
            new_sent = new_sent.__dict__

        if index is not None:
            self.database['products'].update_one({"tags": {"$all": tags}}, {"$set": {f"sents.{index}": new_sent}})
        else:
            self.database['products'].update_one({"tags": {"$all": tags}}, {"$push": {"sents": new_sent}})

    # User Funcs
    def find_or_create_user(self, user_id):
        user = self.database['users'].find_one({"_id": user_id})
        if user is None:
            self.database['users'].insert_one(User(
                user_id,
                wish_list = [],
                premium = False
            ).__dict__)
        return self.database['users'].find_one({"_id": user_id})

    def user_wishes(self, user_id) -> list[Wished]:
        return self.find_or_create_user(user_id)['wish_list']

    def verify_in_user_wish(self, user_id, tag_list, **kwargs):
        all_wishes = kwargs.get("wish_list")
        if all_wishes is None:
            all_wishes = self.user_wishes(user_id)

        for wish in all_wishes:
            if wish['tags'] == tag_list:
                return wish['name']
        
        return False

    def insert_new_user_wish(self, user_id, tag_list, name, category):
        user = self.find_or_create_user(user_id)
        user_wish = user.get('wish_list')
        repeated = self.verify_in_user_wish(user_id, tag_list, wish_list=user_wish)
        if not repeated:
            if len(user_wish) >= 10 and not user.get("premium", False):
                return (False, "Usuário só pode ter até 10 wishes")
            
            new_wish = {
                "name": name,
                "tags": tag_list,
                "category": category
            }
            self.database['users'].update_one({"_id": user_id}, {"$push": {"wish_list": new_wish}})
            self.new_wish(tags=tag_list, user=user_id)
            return (True, "Adicionado com sucesso!")
        else:
            return (False, f"Usuário já tem um alerta igual: {repeated}")

    def remove_user_wish(self, user_id, **kwargs):
        wish_obj = kwargs.get("wish_obj")
        if wish_obj is None:
            name = kwargs.get("name")
            wish_obj = self.database['users'].find_one({"$and": [{"_id": user_id}, {"wish_list.name": name}]})

        tag_list = wish_obj['tags']
        self.database['users'].update_one({"_id": user_id}, {"$pull": {"wish_list": wish_obj}})
        self.remove_wish(tags=tag_list, user=user_id)

    # Wish Funcs
    def new_wish(self, **kwargs):
        tags = kwargs.get('tags')
        user = kwargs.get('user')
        wish_obj = self.find_wish(tags)
        if wish_obj is None:
            self.database['wishes'].insert_one(
                Wished(**kwargs).__dict__
            )
        wish_obj = self.find_wish(tags)
        if user in wish_obj['users']:
            return False
        
        self.database['wishes'].update_one({"tags": {"$all": tags}}, {"$push": {"users": user}})
        return True
    
    def remove_wish(self, **kwargs):
        tags = kwargs.get('tags')
        user = kwargs.get('user')
        wish_obj = self.find_wish(tags)
        if wish_obj is not None:
            self.database['wishes'].update_one({"tags": {"$all": tags}}, {"$pull": {"users": user}})

    def find_wish(self, tags: list):
        return self.database['wishes'].find_one({"tags": {"$all": tags}})
    
    def find_all_wishes(self, tags: list):
        return self.database['wishes'].find({"tags": {"$in": tags}})