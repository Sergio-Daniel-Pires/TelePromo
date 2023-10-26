import time
from dataclasses import dataclass
from typing import Literal


@dataclass
class Link:
    """
    Link objects to store in PyMongo the URL"s that we get products
    """
    name: str
    link: str = ""
    base_repeat: int = 0
    repeat: int = 0
    last: int = None  # timestamp
    status: Literal["NEW", "OK", "ERROR"] = "NEW"
    api_link: str = None

    def __post_init__ (self):
        self.repeat = self.base_repeat
        self.last = int(time.time())

LINKS = [
    {
        "category": "diversified",
        "links": [
            Link("MagaLu")
        ]
    },
    {
        "category": "eletronics",
        "links": [
            Link(
                "Kabum", "https://www.kabum.com.br", 900, api_link="API"
            ),
            Link("Terabyte", "https://www.terabyteshop.com.br/promocoes", 900),
            Link(
                "Pichau", "https://www.pichau.com.br", 900,
                 api_link="https://www.pichau.com.br/api/pichau?query={}"),

            # Aliexpress
            Link("Aliexpress", "https://pt.aliexpress.com/category/201000054/cellphones-telecommunications.html", 900),
            Link("Aliexpress", "https://pt.aliexpress.com/category/201000006/computer-office.html", 900),
            Link("Aliexpress", "https://pt.aliexpress.com/category/201000020/consumer-electronics.html", 900),

            # Shein
            Link("Shein", "https://m.shein.com/br/Consumer-Electronic-c-4671.html", 900),
            Link("Shein", "https://m.shein.com/br/Cell-Phones---Accessories-c-2274.html", 900),
            Link("Shein", "https://m.shein.com/br/Computer---Office-c-2275.html", 900)
        ]
    },
    {
        "category": "clothes",
        "links": [
            Link("Centauro"),
            Link("Dafiti"),
            Link(
                "Nike", "https://www.nike.com.br/_next/data/v10-287-1/nav/ofertas/emoferta.json",
                1800
            ),
            Link(
                "Adidas", "https://www.adidas.com.br/api/plp/content-engine?query=flash_sale", 1800
            ),

            # Aliexpress
            Link("Aliexpress", "https://pt.aliexpress.com/category/201001900/women-clothing.html", 900),
            Link("Aliexpress", "https://pt.aliexpress.com/category/201001892/men-clothing.html", 900),
            Link("Aliexpress", "https://pt.aliexpress.com/category/201003442/women-intimates.html", 900),
            Link("Aliexpress", "https://pt.aliexpress.com/category/201003420/women-accessories.html", 900),
            Link("Aliexpress", "https://pt.aliexpress.com/category/201004457/hair-extensions-wigs.html", 900),
            Link("Aliexpress", "https://pt.aliexpress.com/category/201000219/jewelry-accessories.html", 900),
            Link("Aliexpress", "https://pt.aliexpress.com/category/201000021/beauty-health.html", 900),

            # Shein
            Link("Shein", "https://m.shein.com/br/new/WHATS-NEW-sc-00255950.html", 900),
            Link("Shein", "https://m.shein.com/br/style/Dresses-sc-001148338.html", 900),
            Link("Shein", "https://m.shein.com/br/Women-Tops,-Blouses---Tee-c-1766.html", 900),
            Link("Shein", "https://m.shein.com/br/Women-Bottoms-c-1767.html", 900),
            Link("Shein", "https://m.shein.com/br/Series-recommend/SHEIN-Collection-New-Hot-sc-66798444.html", 900),
            Link("Shein", "https://m.shein.com/br/sale/BR-All-Sale-sc-00510343.html", 900),
            Link("Shein", "https://m.shein.com/br/sale/BR-Blouses-On-Sale-sc-00510353.html", 900),
            Link("Shein", "https://m.shein.com/br/sale/BR-Lingerie-Loungewear-Sale-sc-00544332.html", 900),
            Link("Shein", "https://m.shein.com/br/recommend/Jewelry-sc-100100834.html", 900),
            Link("Shein", "https://m.shein.com/br/Women's-Earrings-c-4202.html", 900),
            Link("Shein", "https://m.shein.com/br/Beauty---Health-c-1864.html", 900),
            Link("Shein", "https://m.shein.com/br/recommend/Makeup-sc-100148871.html?adp=3455673", 900),
            Link("Shein", "https://m.shein.com/br/Wigs---Accs-c-3644.html?adp=5359802", 900),
            Link("Shein", "https://m.shein.com/br/Sexual-Wellness-c-4451.html?adp=14976487", 900),
            Link("Shein", "https://m.shein.com/br/category/Skin-Care-Tools-sc-008132480.html?adp=12505168", 900)
        ]
    },
    {
        "category": "house",
        "links": [
            Link("MadeiraMadeira", "https://www.madeiramadeira.com.br/ofertas-do-dia", 1800),
            Link("Aliexpress", "https://pt.aliexpress.com/category/201000008/home-garden.html", 900),
            Link("Shein", "https://m.shein.com/br/Home---Living-c-2032.html", 900),
            Link("Shein", "https://m.shein.com/br/new/New-in-Storage-and-Organization-sc-00220847.html", 900),
            Link("Shein", "https://m.shein.com/br/category/Shop-By-Kitchen-sc-00815025.html", 900),
            Link("Shein", "https://m.shein.com/br/Event---Party-Supplies-c-2496.html", 900),
            Link("Shein", "https://m.shein.com/br/Home-Essentials-c-1959.html", 900)
        ]
    },
    {
        "category": "pets",
        "links": [
            Link("Cobasi", "https://www.cobasi.com.br/promocoes", 900),
            Link("Aliexpress", "https://pt.aliexpress.com/category/201002447/pet-products.html", 900)
        ]
    },
    {
        "category": "books",
        "links": [
            Link(
                "EstanteVirtual", None, 1800,
                api_link="https://lambda.estantevirtual.com.br/busca/exemplares/{}"
            )
        ]
    }
]
