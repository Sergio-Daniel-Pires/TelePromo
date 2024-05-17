import dataclasses as dc
from typing import Any, Self

import bson

from project.utils import SECONDS_IN_DAY, brand_to_bot


class DatabaseObject():
    def to_insert_data (self) -> dict[str, Any]:
        return self.__dict__

    @classmethod
    def from_dict (cls, data: dict[str, Any]) -> Self:
        if not isinstance(data, dict):
            raise ValueError(f"Param data need to be an mapping, not {type(data)}")

        return cls(**data)

@dc.dataclass()
class Wish(DatabaseObject):
    max: int  = dc.field(default=None)
    min: int  = dc.field(default=None)
    blacklist: list[str] = dc.field(default=None)

@dc.dataclass()
class User(DatabaseObject):
    """
    User object to verify list of wishes and if is premium
    """
    _id: str = dc.field(default=None)
    name: str  = dc.field(default=None)
    max_wishes: int  = dc.field(default=None)
    wish_list: list[Wish] = dc.field(default=None)
    premium: bool = dc.field(default=None)

    def __post_init__ (self):
        """
        Converts nested fields
        """
        if self.wish_list is not None:
            self.wish_list = [ Wish(wish) for wish in self.wish_list ]

@dc.dataclass()
class WishGroup(DatabaseObject):
    """
    Wish object to use in PyMongo
    """
    _id: bson.ObjectId = dc.field(default=None)
    tags: list[str] = dc.field(default=None)
    users: dict[int: Wish] = dc.field(default=None)
    num_wishes: int  = dc.field(default=None)

    def __post_init__ (self):
        if self.users is not None:
            self.users = { key: Wish(wish) for key, wish in self.users.items() }

@dc.dataclass(eq=False)
class Price(DatabaseObject):
    date: int = dc.field(default=None)
    brand: str  = dc.field(default=None)
    price: float = dc.field(default=None)
    original_price: float = dc.field(default=None)
    url: str  = dc.field(default=None)
    img: str  = dc.field(default=None)
    extras: dict[str, Any] = dc.field(default=None)
    details: str  = dc.field(default=None)
    is_promo: bool = dc.field(default=None)
    is_affiliate: bool = dc.field(default=None)
    users_sent: dict[int, int] = dc.field(default=None)

    def __eq__ (self, __value: Self) -> bool:
        if self.days_diff(self.date, __value.date):
            if self.price == __value.price:
                if self.brand == __value.brand:
                    return True

        return False

    @classmethod
    def days_diff (cls, date1: int, date2: int, qtd_days: int = 3):
        return abs((date1 - date2) // 1000) < SECONDS_IN_DAY * qtd_days

@dc.dataclass()
class Product(DatabaseObject):
    """
    Product object to use in PyMongo
    """
    _id: bson.ObjectId = dc.field(default=None)
    raw_name: str  = dc.field(default=None)
    tags: list  = dc.field(default=None)
    category: str  = dc.field(default=None)
    price: float = dc.field(default=None)
    history: list[Price] = dc.field(default=None)

    def __post_init__ (self):
        """
        Converts nested fields
        """
        if self.history is not None:
            self.history = [ Price(price) for price in self.history ]

    def get_history (self) -> list[Price]:
        # Removed from list comprehension, 'extras' fault
        history = []

        for raw_item in self.history:
            if isinstance(raw_item, Price):
                item = raw_item

            elif isinstance(raw_item, dict):
                item = Price.from_dict(raw_item)

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
        return self.tags == __value.tags

    def query_product (self, max_price: None, min_price: None) -> dict[str, Any]:
        query = { "tags": { "$in": [ self.tags ] } }

        if max_price or min_price:
            query["price"] = {}

        if max_price is not None and max_price != 0:
            query["price"].update({ "$lte": max_price * 1.03 })

        if min_price is not None:
            query["price"].update({ "gte": max_price * 0.97 })

    def query_price (self, price_obj: Price) -> dict[str, Any]:
        self.query_product().update({
            "price.date": {
                "gte": ( price_obj.date // 1000 ) - SECONDS_IN_DAY,
                "lte": ( price_obj.date // 1000 ) + SECONDS_IN_DAY,
            }
        })

    def key (self):
        return f"product:{self.tags}"

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
            price_obj.to_insert_data(), product_obj.avarage(), prct_equal, product_obj.raw_name
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

