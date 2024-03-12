import time
from typing import Any

import bson
import pymongo
from pymongo.collection import Collection

from project import config
from project.links import LINKS
from project.metrics_collector import MetricsCollector
from project.models import Price, Product, User, Wish, WishGroup
from project.utils import SECONDS_IN_HOUR


class Database:
    """
    A class to manage connection with python and mongoDB
    """
    client: pymongo.MongoClient
    database: dict[str, Collection]
    metrics_client: MetricsCollector

    def __init__ (
        self, metrics_client: MetricsCollector, mongo_client: pymongo.MongoClient = pymongo.MongoClient
    ):
        self.metrics_client = metrics_client
        self.client = mongo_client(config.MONGO_CONN_STR)
        self.database = self.client["telepromo"]

        self.create_links(LINKS)

    # Product Funcs
    def create_links (self, all_links: list[dict[str, Any]]):
        """
        Create link's entries into database
        """
        for categorys in all_links:
            dict_all_links = [ link.__dict__ for link in categorys["links"] ]
            self.database["links"].find_one_and_update(
                { "category": categorys["category"] },
                { "$set": { "links": dict_all_links } },
                upsert=True
            )

    def get_links (self) -> pymongo.CursorType:
        """
        Retrieve links from database
        """
        links = self.database["links"].find({})
        return links

    def update_link (self, category: str, index: int, status: str, metadata: str):
        """
        Update link in database. On error, increases repeat time to diminuir processing
        """
        time_now = int(time.time())
        base_repeat = metadata["base_repeat"]

        new_fields = {
            f"links.{index}.last": time_now,
            f"links.{index}.status": status
        }

        # reset repeat
        if status == "OK" and metadata["repeat"] != base_repeat:
            new_fields[f"links.{index}.repeat"] = base_repeat

        if status == "ERROR":
            if metadata["repeat"] < SECONDS_IN_HOUR:
                new_fields[f"links.{index}.repeat"] = metadata["repeat"] + 60 * 5

        self.database["links"].update_one(
            { "category": category },
            { "$set": new_fields }
        )

    def get_site_status (self) -> str:
        """
        Show site status to user on chat
        """
        links = self.get_links()

        status_desc = [
            "\n"
            "🟢 - Site funcionando perfeitamente",
            "🔴 - Site com algum problema e/ou fora do ar",
            "⚫ - Ainda não busca nesse site",
        ]
        ok = []
        error = []
        no_link = []

        for category in links:
            for link in category["links"]:
                if link["link"] == "":
                    color = "⚫ - "
                    current_list = no_link
                    extra_info = ""

                elif link["status"] == "ERROR":
                    color = "🔴 - "
                    current_list = error
                    extra_info = ""

                else:
                    color = "🟢 - "
                    current_list = ok

                    extra_info = ""

                msg = color + f"{category['category']}/{link['name']}" + extra_info

                if msg not in current_list:
                    current_list.append(msg)

        return "\n".join(ok + error + no_link + status_desc)

    def find_or_insert_product (self, product: Product) -> tuple[bool, dict[str, Any]]:
        """
        Insert product if was the first time tags appears
        """
        db_product = self.database["products"].find_one({ "tags": { "$all": product.tags } })
        is_new_product = False

        if db_product is None:
            product = product.__dict__
            self.database["products"].insert_one(product)
            is_new_product = True

        else:
            product = db_product

        return is_new_product, product

    def update_product_history (self, tags: list, new_price: dict | Price = None):
        """
        Update product history into database with new price
        """
        if type(new_price) is dict:
            new_price = Price(**new_price)

        price = new_price.price

        self.database["products"].update_one(
            { "tags": {"$all": tags} }, { "$set": { "price": price } }
        )

        if type(new_price) is Price:
            new_price = new_price.__dict__

        self.database["products"].update_one(
            { "tags": { "$all": tags } }, { "$push": { "history": new_price } }
        )

    # User Funcs
    def find_user (self, user_id: int) -> pymongo.CursorType:
        """
        Find an user by user_id
        """
        return self.database["users"].find_one({ "_id": user_id })

    def find_or_create_user (self, user_id: int, user_name: str):
        """
        Return an user, if user not exists yet, creates one.
        """
        new_obj_user = User(
                            user_id, user_name, wish_list=[], premium=False
                        ).__dict__

        user = self.database["users"].find_one_and_update(
            { "_id": user_id },
            {
                "$setOnInsert": new_obj_user
            },
            upsert=True,
            return_document=False
        )

        new_user = False
        if user is None:
            user = new_obj_user
            new_user = True
            self.metrics_client.register_new_user()

        return new_user, user

    # Wish Funcs
    def user_wishes (self, user_id: int, user_name: str) -> list[WishGroup]:
        """
        Return user wishes from user id
        """
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
        self, user_id: str, user_name: str, tag_list: list[str], product: str,
        category: str, max_price: int = 0, min_price: int = 0
    ) -> tuple[bool, str]:
        """
        Verify and insert a new user wish into User model.
        Verifications: Max 15 words, min 1 tag, not repeated wish, max 10 wish per user.
        """
        _, user = self.find_or_create_user(user_id, user_name)
        user_wish = user.get("wish_list")
        max_wishes = user.get("max_wishes", 10)
        repeated = self.verify_repeated_wish(user_id, tag_list, wish_list=user_wish)

        if len(tag_list) >= 15:
            ( False, "Nao pode ter mais que 15 palavras." )

        elif len(tag_list) == 0:
            ( False, "Poucas palavras ou invalidas." )

        elif repeated:
            return ( False, f"Usuário já tem um alerta igual: {repeated}" )

        if len(user_wish) >= max_wishes and not user.get("premium", False):
            return ( False, f"Usuário só pode ter até {max_wishes} wishes" )

        if (min_price > max_price and max_price != 0):
            return ( False, "Preço minimo não pode ser maior que o máximo!" )

        wish_id = self.new_wish(tags=tag_list, user=user_id)

        self.database["users"].update_one(
            { "_id": user_id },
            { "$push": {
                "wish_list": {
                    "wish_id": wish_id,
                    "max": max_price,
                    "min": min_price,
                    "name": product,
                    "tags": tag_list,
                    "category": category,
                    "blacklist": []
                }
            }}
        )

        return (True, "Adicionado com sucesso!")

    def new_wish (self, **kwargs) -> bson.ObjectId:
        """
        Add new wish to WishGroup model
        """
        tags = kwargs.get("tags")
        user_id = kwargs.get("user")

        min_price = kwargs.get("min_price", 0)
        max_price = kwargs.get("max_price", 0)
        user_bl = kwargs.get("blacklist", [])

        wish_obj = self.database["wishes"].find_one_and_update(
            { "tags": tags },
            {
                "$setOnInsert": WishGroup(
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
                "$set": { f"users.{user_id}": Wish(max_price, min_price, user_bl).__dict__ },
                "$inc": { "num_wishes": 1 }
            }

        )
        return wish_id

    def remove_user_wish (self, user_id: int, index: int):
        """
        Remove user wish from User and WishGroup models
        """
        user_obj = self.database["users"].find_one({ "_id": user_id })
        wish_obj = user_obj["wish_list"][index]

        self.database["users"].update_one(
            { "_id": user_id }, { "$pull": { "wish_list": wish_obj } }
        )

        wish_id = wish_obj["wish_id"]
        self.database["wishes"].update_one(
            { "_id": wish_id },
            {
                "$unset": { f"users.{user_id}": 1},
                "$inc": { "num_wishes": -1 }
            }
        )

    def find_all_wishes (self, tags: list[str]) -> list[dict[str, Any]]:
        """
        Find all wishes by tags
        """
        return self.database["wishes"].find(
            { "tags": { "$in": tags } }
        )

    def update_wish_by_index (
        self, user_id: int, index: str, blacklist: list[str] = None,
        lower_price: int | str = None, max_price: int | str = None
    ):
        """
        Update wish price or blacklist
        """
        user_obj = self.database["users"].find_one({ "_id": user_id })
        wish_obj = user_obj["wish_list"]

        if index == -1:
            index = len(wish_obj) - 1

        wish_obj = wish_obj[index]
        wish_id = wish_obj["wish_id"]

        update_on_wishes = {}
        update_on_users = {}
        if max_price:
            max_price = int(max_price)
            update_on_users[f"wish_list.{index}.max"] = max_price
            update_on_wishes[f"users.{user_id}.max"] = max_price

        if lower_price:
            lower_price = int(lower_price)
            update_on_users[f"wish_list.{index}.min"] = lower_price
            update_on_wishes[f"users.{user_id}.min"] = lower_price

        if blacklist:
            update_on_users[f"wish_list.{index}.blacklist"] = blacklist
            update_on_wishes[f"users.{user_id}.blacklist"] = blacklist

        self.database["wishes"].update_one(
            { "_id": wish_id },
            { "$set": update_on_wishes }
        )

        self.database["users"].update_one(
            { "_id": user_id },
            { "$set": update_on_users }
        )

    def verify_or_add_price (
        self, tags: list[str], new_price: Price, product_obj: Product
    ) -> tuple[bool, Price, int]:
        """
        Add price into Product model, if is not repeated price
        """
        history = product_obj.get_history()

        # if Price not in history, are a new price
        try:
            price_index = history.index(new_price)
            is_new_price = False

        except:
            is_new_price = True

        if is_new_price:
            self.update_product_history(tags, new_price)
            return is_new_price, new_price, len(history)

        else:
            return is_new_price, history[price_index], price_index

    def add_new_user_in_price_sent (
        self, product_id: bson.ObjectId, price_idx: int, user_id: int, result: bool
    ) -> None:
        """
        Save user id to don't repeat send
        """
        self.database["products"].update_one(
            { "_id": product_id },
            { "$set": { f"history.{price_idx}.users_sent.{user_id}": result } }
        )
