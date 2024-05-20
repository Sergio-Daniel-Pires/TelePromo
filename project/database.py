import logging
import pickle
import time
from typing import Any

import bson
import pymongo
import redis
from pymongo.collection import Collection

from project import config
from project.links import LINKS
from project.metrics_collector import MetricsCollector
from project.models import Price, Product, User, UserWish, WishGroup
from project.structs import (CreateBaseWish, CreateUser, CreateUserWish,
                             CreateWishGroup)
from project.utils import SECONDS_IN_DAY, SECONDS_IN_HOUR


class Database:
    """
    A class to manage connection with python and mongoDB
    """
    client: pymongo.MongoClient
    database: dict[str, Collection]
    redis_client: redis.Redis
    metrics_client: MetricsCollector

    # Collections
    links: Collection
    products: Collection
    users: Collection
    wishes: Collection

    def __init__ (
        self, metrics_client: MetricsCollector, redis_client: redis.Redis,
        mongo_client: pymongo.MongoClient = pymongo.MongoClient
    ):
        self.metrics_client = metrics_client
        self.client = mongo_client(config.MONGO_CONN_STR)
        self.redis_client = redis_client
        self.database = self.client["telepromo"]

        self.create_links(LINKS)

        # Collections
        self.links = self.database["links"]
        self.products = self.database["products"]
        self.users = self.database["users"]
        self.wishes = self.database["wishes"]

    # Product Funcs
    def create_links (self, all_links: list[dict[str, Any]]):
        """
        Create link's entries into database
        """
        for categorys in all_links:
            dict_all_links = [ link.to_insert() for link in categorys["links"] ]

            self.database.links.find_one_and_update(
                { "category": categorys["category"] },
                { "$set": { "links": dict_all_links } },
                upsert=True
            )

    def get_links (self) -> pymongo.CursorType:
        """
        Retrieve links from database
        """
        links = self.database.links.find({})
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

        self.database.links.update_one(
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

    def find_or_insert_product (self, product_obj: Product) -> tuple[bool, dict[str, Any]]:
        """
        Insert product if was the first time tags appears
        """
        # BUG remove duplicated queries
        raw_product_obj = self.database.products.find_one(
            { "tags": { "$all": product_obj.tags } }
        )

        if raw_product_obj is not None:
            return False, Product.from_dict(raw_product_obj)

        raw_product_obj = self.database.products.insert_one(
            product_obj.to_insert_data()
        )

        return True, product_obj

    def update_product_history (self, tags: list, price_obj: Price):
        """
        Update product history into database with new price
        """
        self.database.products.update_one(
            { "tags": { "$all": tags } }, {
                "$set": { "price": price_obj.price },
                "$push": { "history": price_obj.to_insert_data() }
            }
        )

    # User Funcs
    def find_user (self, user_id: int) -> dict[str, Any]:
        """
        Find an user by user_id
        """
        return self.database.users.find_one({ "_id": user_id })

    def find_or_create_user (self, user_id: int, user_name: str) -> tuple[bool, User]:
        """
        Return an user, if user not exists yet, creates one.
        """
        new_obj_user = CreateUser(user_id, user_name).to_database_obj()

        raw_user = self.database.users.find_one_and_update(
            { "_id": user_id },
            { "$setOnInsert": new_obj_user.to_insert_data() },
            upsert=True,
            return_document=False
        )

        if raw_user is None:
            self.metrics_client.register_new_user()
            return True, new_obj_user

        return False, User.from_dict(raw_user)

    # Wish Funcs
    def user_wishes (self, user_id: int, user_name: str) -> list[UserWish]:
        """
        Return user wishes from user id
        """
        return self.find_or_create_user(user_id, user_name)[1].wish_list

    def verify_repeated_wish (self, user_id, tag_list, **kwargs):
        all_wishes = kwargs.get("wish_list")
        if all_wishes is None:
            all_wishes = self.user_wishes(user_id)

        for wish in all_wishes:
            if wish.tags == tag_list:
                return wish.name

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
        user_wish = user.wish_list
        max_wishes = user.max_wishes
        repeated = self.verify_repeated_wish(user_id, tag_list, wish_list=user_wish)

        if len(tag_list) >= 15:
            ( False, "Nao pode ter mais que 15 palavras." )

        elif len(tag_list) == 0:
            ( False, "Poucas palavras ou invalidas." )

        elif repeated:
            return ( False, f"Usuário já tem um alerta igual: {repeated}" )

        if len(user_wish) >= max_wishes and not user.premium:
            return ( False, f"Usuário só pode ter até {max_wishes} wishes" )

        if (min_price > max_price and max_price != 0):
            return ( False, "Preço minimo não pode ser maior que o máximo!" )

        group_wish_id = self.new_wish_in_group(tags=tag_list, user=user_id)

        self.database.users.update_one(
            { "_id": user_id },
            { "$push": {
                "wish_list": CreateUserWish(
                    group_wish_id, max_price, min_price, product, category, tag_list
                ).to_database_obj().to_insert_data()
            }}
        )

        return ( True, "Adicionado com sucesso!" )

    def new_wish_in_group (self, **kwargs) -> bson.ObjectId:
        """
        Add new wish to WishGroup model
        """
        tags = kwargs.get("tags")
        user_id = kwargs.get("user")

        min_price = kwargs.get("min_price", 0)
        max_price = kwargs.get("max_price", 0)
        user_bl = kwargs.get("blacklist", [])

        wish_group_obj = self.database.wishes.find_one_and_update(
            { "tags": tags },
            {
                "$setOnInsert": CreateWishGroup(tags=tags).to_database_obj().to_insert_data()
            },
            upsert=True, return_document=True
        )
        wish_group_obj = WishGroup.from_dict(wish_group_obj)
        wish_id = wish_group_obj._id

        self.database.wishes.update_one(
            { "_id":  wish_id },
            {
                "$set": {
                    f"users.{user_id}": CreateBaseWish(
                        max_price, min_price, user_bl
                    ).to_database_obj().to_insert_data()
                },
                "$inc": { "num_wishes": 1 }
            }
        )

        return wish_id

    def remove_user_wish (self, user_id: int, index: int):
        """
        Remove user wish from User and WishGroup models
        """
        user_obj = User.from_dict(self.database.users.find_one({ "_id": user_id }))
        user_wish_obj = user_obj.wish_list[index]

        self.database.users.update_one(
            { "_id": user_id }, { "$pull": { "wish_list": user_wish_obj } }
        )

        self.database.wishes.update_one(
            { "_id": user_wish_obj.group_wish_id },
            {
                "$unset": { f"users.{user_id}": 1},
                "$inc": { "num_wishes": -1 }
            }
        )

    def find_all_wishes (self, tags: list[str]) -> list[dict[str, Any]]:
        """
        Find all wishes by tags
        """
        return self.database.wishes.find({ "tags": { "$in": tags } })

    def update_wish_by_index (
        self, user_id: int, index: str, blacklist: list[str] = None,
        min_price: int | str = None, max_price: int | str = None
    ):
        """
        Update wish price or blacklist
        """
        user_obj = User.from_dict(self.database.users.find_one({ "_id": user_id }))
        user_wish_list = user_obj.wish_list

        if index == -1:
            index = len(user_wish_list) - 1

        user_wish_obj = user_wish_list[index]

        update_on_wishes = {}
        update_on_users = {}

        if max_price is not None:
            max_price = int(max_price)
            update_on_users[f"wish_list.{index}.max"] = max_price
            update_on_wishes[f"users.{user_id}.max"] = max_price

        if min_price is not None:
            min_price = int(min_price)
            update_on_users[f"wish_list.{index}.min"] = min_price
            update_on_wishes[f"users.{user_id}.min"] = min_price

        if blacklist is not None:
            update_on_users[f"wish_list.{index}.blacklist"] = blacklist
            update_on_wishes[f"users.{user_id}.blacklist"] = blacklist

        self.database.wishes.update_one(
            { "_id": user_wish_obj.group_wish_id },
            { "$set": update_on_wishes }
        )

        self.database.users.update_one(
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
            return False, history[price_index], price_index

        except ValueError as exc:
            # Update in DB
            self.update_product_history(tags, new_price)

            # Update in-memory
            product_obj.history.append(new_price)

            # Update
            self.redis_client.set(
                product_obj.key(), pickle.dumps(product_obj),
                SECONDS_IN_DAY * 3
            )

            return True, new_price, len(history)

        except Exception as exc:
            logging.error(f"Error {exc} for {tags}: {new_price}")
            raise exc

    def add_new_user_in_price_sent (
        self, product_id: bson.ObjectId, price_idx: int, user_id: int, result: bool
    ) -> None:
        """
        Save user id to don't repeat send
        """
        self.database.products.update_one(
            { "_id": product_id },
            { "$set": { f"history.{price_idx}.users_sent.{user_id}": result } }
        )
