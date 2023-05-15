from typing import Literal, List

class User(object):
    """
    User object to verify list of wishes and if is premium
    """
    _id: str
    wish_list: List[list]
    premium: bool

    def __init__(self, user_id, **kwargs) -> None:
        self._id = user_id
        self.wish_list = kwargs.get("wish_list")
        self.premium = kwargs.get("premium")

class Wished(object):
    """
    Wish object to use in PyMongo
    """
    tags: list
    category: Literal['eletronics']
    num_wishs: int
    links: List[str]
    users: List[str]

    def __init__(self, **kwargs) -> None:
        self.tags = kwargs.get('tags')
        self.category = kwargs.get('category')
        self.num_wishs = 0
        self.links = kwargs.get('link')
        self.users = []

class Price:
    date: str # %d/%m/%y
    price: float
    is_promo: bool
    is_afiliate: bool
    url: str

    def __init__(self, **kwargs) -> None:
        for kwarg in kwargs:
            self.__setattr__(kwarg, kwargs[kwarg])

    def __eq__(self, __value: object) -> bool:
        if self.date == __value.date:
            if self.price == __value.price:
                if self.url == __value.url:
                    return True
        
        return False

class Product(object):
    """
    Product object to use in PyMongo
    """
    raw_name: str
    tags: list
    price: str
    history: List[Price]
    sents: List[Price]

    def __init__(self, **kwargs) -> None:
        self.raw_name = kwargs.get('raw_name')
        self.tags = kwargs.get('tags')
        self.price = kwargs.get('price')
        self.history = kwargs.get('history')
        self.sents = []

    def avarage(history: dict) -> float:
        values = [value['price'] for value in history]
        return sum(values)/len(values)

class Links(object):
    """
    Link objects to store in PyMongo the URL's that we get products
    """
    name: str
    links: dict
    repeat: int # time in Seconds
    last: str # in datetime %d/%m/%y %H:%M

    def __init__(self, **kwargs) -> None:
        self.name = kwargs.get('name')
        self.links = kwargs.get('links')
        self.repeat = kwargs.get('repeat')
        self.last = None