import asyncio
from enum import Enum
from typing import Any

import requests
from playwright.async_api import Page

try:
    from project.bots import base

except Exception:
    import base

class CasasBahiaMessages(str, Enum):
    ALL_TAGS_MATCHED = (
        "*{brand}*: OFERTA PRA VOCÊ! 😱😱\n"
        "\n"
        "🔥🔥🔥 {name}, {details}\n"
        "{condition}"
        "{warranty}"
        "\n"
        "Preço 💵\n"
        "R$ {price:.2f} {installment}"
        "\n"
        "{shipping}"
        "\n"
    )

    AVG_LOW = (
        "*{brand}*: Baixou de preco!\n"
        "\n"
        "🔥🔥 {name}, {details}\n"
        "{condition}"
        "{warranty}"
        "\n"
        "Preço 💵\n"
        "R$ {price:.2f} {installment}"
        "Hist.: {avg}\n"                     # AVG Price
        "\n"
        "{shipping}"
        "\n"
    )

    MATCHED_OFFER = (
        "*{brand}*: Você também pode gostar!\n"
        "\n"
        "🔥 {name}, {details}\n"
        "{condition}"
        "{warranty}"
        "\n"
        "Preço 💵\n"
        "R$ {price:.2f} {installment}"
        "\n"
        "{shipping}"
        "\n"
    )

class CasasBahia (base.BotRunner):
    messages: Enum = CasasBahiaMessages

    def __init__(
        self, link: str, index: int, category: str, messages: Enum = ...,
        metadata: dict[str, Any] = {}, api_link: str = None
    ) -> None:
        super().__init__(link, index, category, messages, metadata, api_link)
        self.messages = CasasBahiaMessages

    async def get_prices (self, page: Page):
        return []

    async def get_prices_from_api(self):
        results = []

        headers = {
            "Xaplication": "vv-categoria-frontend",
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/119.0.0.0 Safari/537.36"
            )
        }

        response = requests.get(self.api_link, headers=headers).json()

        products = []
        product_ids = []
        for product in response["products"]:
            status = product["status"]
            if status != "AVAILABLE":
                print(status)
                continue

            products.append({
                "name": product["name"], "img": product["image"],
                "url": product["url"], "details": "", "extras": {}
            })
            product_ids.append(product["id"])

        product_prices_url = (
            "https://api.casasbahia.com.br/merchandising/oferta/v1/Preco/Produto/PrecoVenda/"
            "?idsProduto={}&composicao=DescontoFormaPagamento%2CMelhoresParcelamentos&"
            "apiKey=d081fef8c2c44645bb082712ed32a047"
        ).format(",".join(product_ids))

        prices = requests.get(product_prices_url, headers=headers).json()

        print(prices)

        for offer, price_obj in zip(products, prices["PrecoProdutos"]):
            price_obj = price_obj["PrecoVenda"]
            offer["price"] = price_obj["Preco"]
            offer["original_price"] = price_obj["PrecoDe"]
            offer["extras"]["installment"] = price_obj["Parcelamento"]

            results.append(
                self.new_product(**offer)
            )

        return results

if __name__ == "__main__":
    ready_pages = [ CasasBahia(
        link="", index=0, category="house",
        api_link="https://prd-api-partner.viavarejo.com.br/api/v2/Search?ResultsPerPage=1000&PartnerKey=solr&ApiKey=casasbahia&Filter=D80371&Page=1&banner=true&PlatformType=1&Filtro=D80371&PaginaAtual=1"
    ) ]
    results = asyncio.run(base.BotBase(ready_pages, True).run())

    print(results)
    import json
    with open("casas_vadias.json", "w") as json_file:
       json.dump(results, json_file)
