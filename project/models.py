import importlib
from typing import Any

import bson

from project.utils import SECONDS_IN_DAY, name_to_object


class User:
    """
    User object to verify list of wishes and if is premium
    """
    _id: str
    name: str
    wish_list: dict[str, str]
    premium: bool

    def __init__ (self, user_id: str, user_name: str, **kwargs) -> None:
        self._id = user_id
        self.name = user_name
        self.wish_list = kwargs.get("wish_list", [])
        self.premium = kwargs.get("premium", False)

class Wished:
    """
    Wish object to use in PyMongo
    """
    _id: bson.ObjectId
    tags: list[str]
    adjectives: list[str]
    users: dict[int: float | int]
    max_wishes: int
    num_wishs: int

    def __init__ (self, **kwargs) -> None:
        self._id = bson.ObjectId()
        self.tags = kwargs.get("tags")
        self.tags = kwargs.get("adjectives")
        self.users = kwargs.get("users", {})
        self.num_wishs = 0
        self.max_wishes = 10

class Price:
    _id: bson.ObjectId()
    date: int           # time stamp
    price: float
    old_price: float
    is_promo: bool
    is_affiliate: bool
    url: str
    users_sent: dict[int, int]
    extras: dict[str, Any]

    def __init__ (
        self, date: int, price: float, old_price: float, is_promo: bool, is_affiliate: bool,
        url: str, extras: dict[str, Any] = {}, users_sent: dict[int, int] = {},
        _id: bson.ObjectId = None
    ) -> None:
        if not isinstance(_id, bson.ObjectId):
            _id = bson.ObjectId()

        self._id = _id
        self.date = date
        self.price = price
        self.old_price = old_price
        self.is_promo = is_promo
        self.is_affiliate = is_affiliate
        self.url = url
        self.users_sent = users_sent

        self.extras = extras

    def __eq__ (self, __value: object) -> bool:
        if (self.date - __value.date) < SECONDS_IN_DAY * 3:
            if self.price == __value.price:
                if self.url == __value.url:
                    return True

        return False

class Product:
    """
    Product object to use in PyMongo
    """
    _id: bson.ObjectId()
    raw_name: str
    tags: list
    adjectives: list
    category: str
    price: float
    history: list[Price]

    def __init__ (
        self, raw_name: str, tags: list, adjectives: list, category: str, price: float,
        history: list[Price] = [], _id: bson.ObjectId = None
    ) -> None:
        if not isinstance(_id, bson.ObjectId):
            _id = bson.ObjectId()

        self._id = _id
        self.raw_name = raw_name
        self.tags = tags
        self.adjectives = adjectives
        self.category = category
        self.price = price
        self.history = history

    def get_history (self) -> list[Price]:
        # Removed from list comprehension, 'extras' fault
        return [Price(**items) for items in self.history]

    def avarage (self) -> float:
        values = [float(value.price) for value in self.get_history()]
        if len(values) == 0:
            return 0

        return sum(values)/len(values)

class FormatPromoMessage:
    """
    Object that formats user message
    """
    result: dict
    avarage: float
    prct_equal: float

    @classmethod
    def parse_msg (
        cls, result: dict[str, Any], avarage: float, prct_equal: float, bot_name: str,
    ):
        brand = result["brand"]
        img = result["img"]
        url = result["url"]

        # Get custom promo message if needed
        bot_instance = name_to_object[bot_name]
        output_msg = bot_instance.promo_message(result, avarage, prct_equal)

        output = cls.escape_msg(output_msg)

        output += f"[ \u206f ]({img})\n"
        output += f"🛒 [\[COMPRAR NA {brand.upper()}\]]({url})\n"  # noqa W605 # type: ignore
        return output

    @classmethod
    def escape_msg (cls, output: str):
        # escape special chars:
        for char in (".", "!", "(", ")", "-", "_", "+", "#"):
            output = output.replace(char, rf"\{char}")

        return output
