import pytest


@pytest.fixture
def iphone_offer ():
    return {
        "brand": "Aliexpress",
        "category": "eletronics",
        "name": "iPhone X 256gb preto 12mp ios",
        "details": "",
        "price": 1000,
        "old_price": 1000,
        "url": "https://pt.aliexpress.com/item/1005005763852503.html",
        "img": "https://ae01.alicdn.com/kf/S6830462bb94f4a9089aa1de5973f29a3S.jpg",
        "extras": {
            "shipping": "Consulte o frete!"
        }
    }

@pytest.fixture
def bed_offer ():
    return {
        "brand": "Magalu",
        "category": "eletronics",
        "name": "Cabeceira para cama de casal queen size",
        "details": "",
        "price": 1000,
        "old_price": 1000,
        "url": "https://pt.aliexpress.com/item/1005005763852503.html",
        "img": "https://ae01.alicdn.com/kf/S6830462bb94f4a9089aa1de5973f29a3S.jpg",
        "extras": {}
    }

@pytest.fixture
def redis_client(request):
    import fakeredis
    redis_client = fakeredis.FakeRedis()
    return redis_client

