import bson
from project.links import LINKS
from project.models import Price, Product, User, Wished
import pymongo
from pymongo.collection import Collection
import os
from project.metrics_collector import MetricsCollector
import time


class Database:
    """
    A class to manage connection with python and mongoDB
    """
    client: pymongo.MongoClient
    database: dict[str, Collection]
    metrics_client: MetricsCollector

    def __init__ (self, metrics_client: MetricsCollector):
        self.metrics_client = metrics_client
        self.client = pymongo.MongoClient(
            f"mongodb://{os.environ.get('MONGO_URL', 'localhost')}",
            os.environ.get("MONGO_PORT", 27017)
        )
        self.database = self.client["telepromo"]

        # Initialize collections
        # if "links" not in self.database.list_collection_names():
        self.create_links(LINKS)

    # Product Funcs
    def create_links (self, all_links: list):
        for link in all_links:
            self.database["links"].find_one_and_update(
                { "category": link["category"] },
                { "$set": { "links": link["links"] } },
                upsert=True
            )

    def get_links (self):
        links = self.database["links"].find({})
        return links

    def update_link (self, category: str, index: int):
        time_now = int(time.time())

        self.database["links"].update_one(
            { "category": category },
            { "$set": { f"links.{index}.last": time_now } }
        )

    def find_product (self, product: Product) -> tuple[bool, dict]:
        dict_product = self.database["products"].find_one(
            { "tags": { "$all": product.tags } }
        )
        new_product = False

        if dict_product is None:
            self.database["products"].insert_one(product.__dict__)
            dict_product = product.__dict__
            new_product = True

        return new_product, dict_product

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
        new_obj_user = User(
                            user_id, user_name, wish_list=[], premium=False
                        )

        user = self.database["users"].find_one_and_update(
            { "_id": user_id },
            {
                "$setOnInsert": new_obj_user.__dict__
            },
            upsert=True,
            return_document=False
        )

        new_user = False
        if user is None:
            user = new_obj_user.__dict__
            new_user = True
            self.metrics_client.register_new_user()

        return new_user, user

    # Wish Funcs
    def user_wishes (self, user_id: int, user_name: str) -> list[Wished]:
        return self.find_or_create_user(user_id, user_name)[1]["wish_list"]

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

        _, user = self.find_or_create_user(user_id, user_name)
        user_wish = user.get("wish_list")
        repeated = self.verify_repeated_wish(user_id, tag_list, wish_list=user_wish)
        if len(tag_list) >= 15:
            (False, "Nao pode ter mais que 15 palavras.")

        elif len(tag_list) == 0:
            (False, "Poucas palavras ou invalidas.")

        elif repeated:
            return (False, f"Usuário já tem um alerta igual: {repeated}")

        if len(user_wish) >= 10 and not user.get("premium", False):
            return (False, "Usuário só pode ter até 10 wishes")

        wish_id = self.new_wish(tags=tag_list, user=user_id)

        self.database["users"].update_one(
            { "_id": user_id },
            { "$push": {
                "wish_list": {
                    "wish_id": wish_id,
                    "max": max_price,
                    "name": product,
                    "tags": tag_list,
                    "category": category
                }
            }}
        )

        return (True, "Adicionado com sucesso!")

    def new_wish (self, **kwargs):
        tags = kwargs.get("tags")
        user_id = kwargs.get("user")

        wish_obj = self.database["wishes"].find_one_and_update(
            { "tags": tags },
            {
                "$setOnInsert": Wished(
                                    tags=tags
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

    def update_wish_by_index (self, user_id: int, value: str, index: str):
        value = int(value)

        user_obj = self.database["users"].find_one(
            { "_id": user_id }
        )
        wish_obj = user_obj["wish_list"]
        if index == -1:
            index = len(wish_obj) - 1

        wish_obj = wish_obj[index]
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
