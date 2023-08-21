from pymongo import MongoClient
import bson

from bots.base import LINKS
from models import Wished, User, Price, Product

class Database:
    """
    A class to manage connection with python and mongoDB
    """

    client = MongoClient
    database = dict

    def __init__ (self):
        self.client = MongoClient("mongodb://localhost", 27017)
        self.database = self.client["telepromo"]

        # Initialize collections
        if "links" not in self.database.list_collection_names():
            self.database["links"].insert_many(LINKS)

    # Product Funcs
    def get_links (self):
        links = self.database["links"].find({})
        return links

    def find_product (self, product: Product):
        dict_product = self.database["products"].find_one_and_update(
            { "tags": product.tags },
            { "$setOnInsert": product.__dict__ },
            upsert=True,
            return_document=True
        )

        old_product = not bool(len(dict_product["history"]) - 1)
        return old_product, dict_product

    def update_product_history (
        self, tags: list, new_price: dict | Price = None
    ) -> None:
        if type(new_price) is dict:
            new_price = Price(**new_price)

        price = new_price.price

        self.database["products"].update_one({"tags": {"$all": tags}}, {"$set": {"price": price}})

        if type(new_price) is Price:
            new_price = new_price.__dict__

        self.database["products"].update_one(
            {"tags": {"$all": tags}}, {"$push": {"history": new_price}}
        )

    def find_user (self, user_id: int):
        return self.database["users"].find_one({ "_id": user_id })

    # User Funcs
    def find_or_create_user (self, user_id: int, user_name: str):
        user = self.database["users"].find_one_and_update(
            { "_id": user_id },
            {
                "$setOnInsert": User(
                                    user_id, user_name, wish_list=[], premium=False
                                ).__dict__
            },
            upsert=True,
            return_document=True
        )

        return user

    # Wish Funcs
    def user_wishes (self, user_id: int, user_name: str) -> list[Wished]:
        return self.find_or_create_user(user_id, user_name)["wish_list"]

    def verify_repeated_wish (self, user_id, tag_list, **kwargs):
        all_wishes = kwargs.get("wish_list")
        if all_wishes is None:
            all_wishes = self.user_wishes(user_id)

        for wish in all_wishes:
            if wish["tags"] == tag_list:
                return wish["name"]

        return False

    def insert_new_user_wish (
        self, user_id, user_name, tag_list, product, category, max_price=0
    ) -> tuple[bool, str]:

        user = self.find_or_create_user(user_id, user_name)
        user_wish = user.get("wish_list")
        repeated = self.verify_repeated_wish(user_id, tag_list, wish_list=user_wish)

        if not repeated:
            if len(user_wish) >= 10 and not user.get("premium", False):
                return (False, "Usuário só pode ter até 10 wishes")

            wish_id = self.new_wish(tags=tag_list, user=user_id, category=category)

            self.database["users"].update_one(
                { "_id": user_id },
                { "$push": {
                    "wish_list": {
                        "wish_id": wish_id,
                        "max": max_price,
                        "name": product,
                        "tags": tag_list
                    }
                }}
            )

            return (True, "Adicionado com sucesso!")

        else:
            return (False, f"Usuário já tem um alerta igual: {repeated}")

    def new_wish (self, **kwargs):
        tags = kwargs.get("tags")
        user_id = kwargs.get("user")
        category = kwargs.get("category")

        wish_obj = self.database["wishes"].find_one_and_update(
            { "tags": tags },
            {
                "$setOnInsert": Wished(
                                    tags=tags, category=category
                                ).__dict__
            },
            upsert=True,
            return_document=True
        )

        wish_id = wish_obj["_id"]

        wish_obj = self.database["wishes"].update_one(
            { "_id":  wish_id },
            {
                "$set": { f"users.{user_id}": 0 },
                "$inc": { "num_wishs": 1 }
            }
        )

        return wish_id

    def remove_user_wish (self, user_id: int, index: int):
        user_obj = self.database["users"].find_one(
            {"_id": user_id}
        )
        wish_obj = user_obj["wish_list"][index]

        self.database["users"].update_one(
            { "_id": user_id }, { "$pull": { "wish_list": wish_obj } }
        )

        wish_id = wish_obj["wish_id"]
        self.database["wishes"].update_one(
            { "_id": wish_id },
            {
                "$unset": { f"users.{user_id}": 1},
                "$inc": { "num_wishs": -1 }
            }
        )

    def find_all_wishes (self, tags: list):
        return self.database["wishes"].find(
            { "tags": { "$in": tags } }
        )

    def update_last (self, user_id: int, value: str):
        value = int(value)

        user_obj = self.database["users"].find_one(
            { "_id": user_id }
        )
        wish_obj = user_obj["wish_list"]
        index = len(wish_obj) - 1
        wish_obj = wish_obj[-1]
        wish_id = wish_obj["wish_id"]

        self.database["users"].update_one(
            { "_id": user_id }, { "$set": { f"wish_list.{index}.max": value } }
        )

        self.database["wishes"].update_one(
            { "_id": wish_id },
            { "$set": { f"users.{user_id}": value } }
        )

    def verify_or_add_price (
        self, tags: list[str], new_price: dict | Price, product_obj: Product
    ) -> tuple[bool, Price, int]:
        history = product_obj.get_history()
        is_new_price = new_price not in history

        if is_new_price:
            self.update_product_history(tags, new_price)
            return is_new_price, new_price, len(history)

        else:
            index = history.index(new_price)
            return is_new_price, history[index], index

    def add_new_user_in_price_sent (
        self, product_id: bson.ObjectId(), price_idx: int, user_id: int, result: bool
    ) -> None:
        self.database["products"].update_one(
            { "_id": product_id },
            { "$set": { f"history.{price_idx}.users_sent.{user_id}": result } }
        )
