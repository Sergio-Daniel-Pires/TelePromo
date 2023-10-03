from dataclasses import dataclass
from typing import Literal
import time

@dataclass
class Link:
    """
    Link objects to store in PyMongo the URL"s that we get products
    """
    name: str
    link: str           = ""
    base_repeat: int    = 0
    repeat: int         = 0
    last: int           = None # timestamp
    status: Literal["NEW", "OK", "ERROR"] = "NEW"

    def __post_init__ (self):
        self.repeat = self.base_repeat
        self.last = int(time.time())

LINKS = [
    {
        "category": "diversificado",
        "links": [
            Link("MagaLu")
        ]
    },
    {
        "category": "eletronicos",
        "links": [
            Link("Kabum", "https://www.kabum.com.br/ofertas/SETEMBROTECH", 900),
            Link("Terabyte", "https://www.terabyteshop.com.br/promocoes", 900),
            Link("Pichau", "https://www.pichau.com.br/", 900),
            Link("Aliexpress", "https://pt.aliexpress.com/category/201000054/cellphones-telecommunications.html", 300),
            Link("Aliexpress", "https://pt.aliexpress.com/category/201000006/computer-office.html", 300),
            Link("Aliexpress", "https://pt.aliexpress.com/category/201000020/consumer-electronics.html", 300)
        ]
    },
    {
        "category": "roupas",
        "links": [
            Link("Centauro"),
            Link("Dafiti"),
            Link("Nike", "https://www.nike.com.br/nav/ofertas/emoferta", 1800),
            Link("Adidas", "https://www.adidas.com.br/flash_sale", 1800),
            Link("Aliexpress", "https://pt.aliexpress.com/category/201001900/women-clothing.html", 300),
            Link("Aliexpress", "https://pt.aliexpress.com/category/201001892/men-clothing.html", 300),
            Link("Aliexpress", "https://pt.aliexpress.com/category/201003442/women-intimates.html", 300),
            Link("Aliexpress", "https://pt.aliexpress.com/category/201003420/women-accessories.html", 300),
            Link("Aliexpress", "https://pt.aliexpress.com/category/201004457/hair-extensions-wigs.html", 300),
            Link("Aliexpress", "https://pt.aliexpress.com/category/201000219/jewelry-accessories.html", 300),
            Link("Aliexpress", "https://pt.aliexpress.com/category/201000021/beauty-health.html", 300)
        ]
    },
    {
        "category": "casa/domestico",
        "links": [
            Link("MadeiraMadeira", "https://www.madeiramadeira.com.br/ofertas-do-dia", 1800),
            Link("Aliexpress", "https://pt.aliexpress.com/category/201000008/home-garden.html", 300)
        ]
    },
    {
        "category": "pets",
        "links": [
            Link("Cobasi", "https://www.cobasi.com.br/promocoes", 900),
            Link("Aliexpress", "https://pt.aliexpress.com/category/201002447/pet-products.html", 300)
        ]
    },
    {
        "category": "livros",
        "links": [
            Link("EstanteVirtual")
        ]
    }
]
