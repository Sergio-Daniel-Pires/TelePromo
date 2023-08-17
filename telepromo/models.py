from typing import Literal, List
from typing import Optional

from main import SECONDS_IN_DAY

class User:
    """
    User object to verify list of wishes and if is premium
    """
    _id: str
    wish_list: List[dict]
    premium: bool

    def __init__ (self, user_id, **kwargs) -> None:
        self._id = user_id
        self.wish_list = kwargs.get("wish_list", [])
        self.premium = kwargs.get("premium", False)

class Wished:
    """
    Wish object to use in PyMongo
    """
    tags: list
    category: Literal["eletronics", None]
    num_wishs: int
    links: List[str]
    users: List[str]

    def __init__ (self, **kwargs) -> None:
        self.tags = kwargs.get("tags")
        self.category = kwargs.get("category")
        self.num_wishs = 0
        self.links = kwargs.get("link")
        self.users = []

class Price:
    date: int  # time stamp
    price: float
    is_promo: bool
    is_afiliate: bool
    url: str
    users: Optional[list[str]]

    def __init__ (self, **kwargs) -> None:
        for kwarg in kwargs:
            self.__setattr__(kwarg, kwargs[kwarg])

    def __eq__ (self, __value: object) -> bool:
        if abs((self.date - __value.date) // ) < 3:
            if self.price == __value.price:
                if self.url == __value.url:
                    return True

        return False

class Product:
    """
    Product object to use in PyMongof
    """
    raw_name: str
    tags: list
    category: str
    price: str
    history: List[Price]
    sents: List[Price]

    def __init__ (self, **kwargs) -> None:
        self.raw_name = kwargs.get("raw_name")
        self.tags = kwargs.get("tags")
        self.category = kwargs.get("category")
        self.price = kwargs.get("price")
        self.history = kwargs.get("history")
        self.sents = kwargs.get("sents", [])

    def get_history (self) -> list[Price]:
        return [Price(**items) for items in self.history]

    def get_sents (self) -> list[Price]:
        return [Price(**items) for items in self.sents]

    def avarage (self) -> float:
        values = [float(value.price) for value in self.get_history()]
        return sum(values)/len(values)

    def verify_in_history (self, new_price: dict | Price) -> bool:
        if type(new_price) is dict:
            new_price = Price(**new_price)

        return new_price in self.get_history()

    def verify_get_in_sents (self, new_price: dict | Price) -> bool:
        if type(new_price) is dict:
            new_price = Price(**new_price)

        try:
            return self.get_sents().index(new_price)

        except Exception:
            return None

class Links:
    """
    Link objects to store in PyMongo the URL"s that we get products
    """
    name: str
    links: dict
    repeat: int     # time in Seconds
    last: int       # in timestamp

    def __init__ (self, **kwargs) -> None:
        self.name = kwargs.get("name")
        self.links = kwargs.get("links")
        self.repeat = kwargs.get("repeat")
        self.last = None