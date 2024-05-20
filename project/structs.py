import dataclasses as dc
import time
from typing import Any

import bson

from project.models import BaseWish, Price, Product, User, UserWish, WishGroup


@dc.dataclass()
class CreateBaseWish:
    max: int
    min: int = dc.field(default=0)
    blacklist: list[str] = dc.field(default_factory=list)

    def to_database_obj (self):
        return BaseWish(**self.__dict__)

@dc.dataclass()
class CreateUserWish:
    group_wish_id: str
    max: str
    min: str
    name: str
    category: str
    tags: list[str] = dc.field(default_factory=list)
    blacklist: list[str] = dc.field(default_factory=list)

    def to_database_obj (self):
        return UserWish(**self.__dict__)

@dc.dataclass()
class CreateUser:
    """
    User object to verify list of wishes and if is premium
    """
    _id: str
    name: str
    wish_list: list[UserWish] = dc.field(default_factory=list)
    max_wishes: int = dc.field(default=10)
    premium: bool = dc.field(default=False)

    def to_database_obj (self) -> User:
        return User(**self.__dict__)

@dc.dataclass()
class CreateWishGroup:
    """
    Wish object to use in PyMongo
    """
    tags: list[str] = dc.field(default_factory=list)
    users: dict[int: BaseWish] = dc.field(default_factory=dict)
    num_wishes: int = dc.field(default=0)

    def to_database_obj (self):
        return WishGroup(
            _id=bson.ObjectId(),
            **self.__dict__
        )

@dc.dataclass(eq=False)
class CreatePrice:
    brand: str
    price: float
    original_price: float
    url: str
    img: str
    extras: dict[str, Any] = dc.field(default_factory=dict)
    details: str = dc.field(default="")
    is_promo: bool = dc.field(default=False)
    is_affiliate: bool = dc.field(default=None)
    users_sent: dict[int, int] = dc.field(default_factory=dict)

    def to_database_obj (self):
        return Price(
            date=int(time.time() * 1000),
            **self.__dict__
        )

@dc.dataclass()
class CreateProduct:
    """
    Product object to use in PyMongo
    """
    raw_name: str
    category: str
    price: float
    tags: list = dc.field(default_factory=list)
    history: list[Price] = dc.field(default_factory=list)

    def to_database_obj (self):
        return Product(
            _id=bson.ObjectId(),
            **self.__dict__
        )
