from typing import Literal

class Wished(object):
    """
    Wish object to use in PyMongo
    """
    tags: list
    category: Literal['eletronics']
    num_wishs: int
    links: list[str]
    users: list[str]

    def __init__(self, tags: list, category: str, links: list = []) -> None:
        self.tags = tags
        self.category = category
        self.num_wishs = 0
        self.links = []
        self.users = []

class Sent:
    date: str
    price: float
    is_promo: bool
    is_afiliate: bool
    url: str

    def __init__(self, **kwargs) -> None:
        for kwarg in kwargs:
            self.__setattr__(kwarg, kwargs[kwarg])

class Product(object):
    """
    Product object to use in PyMongo
    """
    raw_name: str
    tags: list
    price: str
    sents: list[Sent]

    def __init__(self, raw_name: str, tags: list, price: float) -> None:
        self.raw_name = raw_name
        self.tags = tags
        self.price = price
        self.sents = []

class Links(object):
    """
    Link objects to store in PyMongo the URL's that we get products
    """
    name: str
    links: dict

    def __init__(self, name: str) -> None:
        self.name = name
        self.links = {}

    def list_links(self):
        ...