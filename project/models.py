import time
from typing import Any

import bson

from project.utils import SECONDS_IN_DAY, brand_to_bot


class User:
    """
    User object to verify list of wishes and if is premium
    """
    _id: str
    name: str
    max_wishes: int
    wish_list: dict[str, str]
    premium: bool

    def __init__ (self, user_id: str, user_name: str, **kwargs) -> None:
        self._id = user_id
        self.name = user_name
        self.wish_list = kwargs.get("wish_list", [])
        self.max_wishes = kwargs.get("max_wishes", 10)
        self.premium = kwargs.get("premium", False)

class Wish:
    price: float | int
    blacklist: list[str]

    def __init__(
        self, price: float | int, blacklist: list[str] = []
    ) -> None:
        self.price = price
        self.blacklist = blacklist

class WishGroup:
    """
    Wish object to use in PyMongo
    """
    _id: bson.ObjectId
    tags: list[str]
    users: dict[int: Wish]
    num_wishs: int

    def __init__ (self, **kwargs) -> None:
        self._id = bson.ObjectId()
        self.tags = kwargs.get("tags")
        self.users = kwargs.get("users", {})
        self.num_wishs = 0

class Price:
    _id: bson.ObjectId
    brand: str
    price: float
    old_price: float
    url: str
    img: str
    extras: dict[str, Any]
    details: str
    is_promo: bool
    is_affiliate: bool
    users_sent: dict[int, int]

    def __init__ (
        self, price: float, old_price: float, is_promo: bool, is_affiliate: bool,
        url: str, brand: str, img: str, extras: dict[str, Any] = None, date = None,
        users_sent: dict[int, int] = None, _id: bson.ObjectId = None, details = None
    ) -> None:
        if not isinstance(_id, bson.ObjectId):
            _id = bson.ObjectId()

        self._id = _id
        self.date = date if date is not None else int(time.time() * 1000)
        self.price = price
        self.old_price = old_price
        self.is_promo = is_promo
        self.is_affiliate = is_affiliate
        self.url = url
        self.brand = brand
        self.img = img
        self.users_sent = users_sent if users_sent is not None else {}

        self.extras = extras if extras is not None else {}

        self.details = details if details is not None else ""

    def __eq__ (self, __value: object) -> bool:
        if abs((self.date - __value.date) // 1000) < SECONDS_IN_DAY * 3:
            if self.price == __value.price:
                if self.url == __value.url:
                    if self.brand == __value.brand:
                        return True

        return False

class Product:
    """
    Product object to use in PyMongo
    """
    _id: bson.ObjectId
    raw_name: str
    tags: list
    adjectives: list
    category: str
    price: float
    history: list[Price]

    def __init__ (
        self, raw_name: str, tags: list, adjectives: list, category: str, price: float,
        history: list[Price] = None, _id: bson.ObjectId = None
    ) -> None:
        if not isinstance(_id, bson.ObjectId):
            _id = bson.ObjectId()

        self._id = _id
        self.raw_name = raw_name
        self.tags = tags
        self.adjectives = adjectives
        self.category = category
        self.price = price
        self.history = history if history is not None else []

    def get_history (self) -> list[Price]:
        # Removed from list comprehension, 'extras' fault
        history = []

        for raw_item in self.history:
            if isinstance(raw_item, Price):
                item = raw_item

            elif isinstance(raw_item, dict):
                item = Price(**raw_item)

            else:
                raise TypeError(f"{raw_item} is not a valid Price")

            history.append(item)

        return history

    def avarage (self) -> float:
        values = [ float(value.price) for value in self.get_history() ]

        if len(values) == 0:
            return 0

        return sum(values)/len(values)

    def __eq__(self, __value: object) -> bool:
        if self.tags == __value.tags:
            return True

        else:
            False

class FormatPromoMessage:
    """
    Object that formats user message
    """
    result: Price
    avarage: float
    prct_equal: float

    @classmethod
    def parse_msg (
        cls, price_obj: Price, product_obj: Product, prct_equal: float
    ) -> str:
        img = price_obj.img
        url = price_obj.url

        # Get custom promo message if needed
        bot_instance = brand_to_bot[price_obj.brand]
        output_msg = bot_instance.promo_message(
            price_obj.__dict__, product_obj.avarage(), prct_equal, product_obj.raw_name
        )

        output = cls.escape_msg(output_msg)

        output += f"[ \u206f ]({img})\n"
        output += f"🛒 [\\[COMPRAR NA {price_obj.brand.upper()}\\]]({url})\n"  # W605 type: ignore

        return output

    @classmethod
    def escape_msg (cls, output: str) -> str:
        # escape special chars:
        for char in (".", "!", "(", ")", "-", "_", "+", "#"):
            output = output.replace(char, rf"\{char}")

        return output
