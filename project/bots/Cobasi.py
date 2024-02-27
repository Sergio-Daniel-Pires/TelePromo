import asyncio
import logging
import re
import traceback
from enum import Enum
from typing import Any

import requests
from playwright.async_api import Page

from project.bots.base import UserMessages

try:
    from project.bots import base
except Exception:
    import base

class CobasiMessages(str, Enum):
    ALL_TAGS_MATCHED = (
        "*{brand}*: OFERTA PRA VOCÊ! 🐶😺\n"   # Site name
        "\n"
        "🔥🔥🔥 {name}\n"                           # Product name
        "\n"
        "Preço 💵\n"
        "R$ {price:.2f}"                          # Price
        "\n"
        "\n"
        "🐶 Amigo Cobasi\n"
        "R$ {sub_price:.2f}"                          # Prime price
        "\n"
    )

    AVG_LOW = (
        "*{brand}*: Baixou de preco!\n"        # Site name
        "\n"
        "🔥🔥 {name}\n"                       # Product name
        "Preço 💵\n"
        "\n"
        "R$ {price:.2f}\n"                  # Price
        "Hist.: {avg}\n"                     # AVG Price
        "\n"
        "\n"
        "🐶 Amigo Cobasi\n"
        "R$ {sub_price:.2f}"                    # Prime price
        "\n"
    )

    MATCHED_OFFER = (
        "*{brand}*: Recomendado pro seu Pet!\n"    # Site name
        "\n"
        "🔥 {name}\n"                        # Product name
        "Preço 💵\n"
        "R$ {price:.2f}"                   # Price
        "\n"
        "\n"
        "🐶 Amigo Cobasi\n"
        "R$ {sub_price:.2f}"                   # Prime price
        "\n"
    )

class Cobasi (base.BotRunner):
    messages: Enum = CobasiMessages

    def __init__(
        self, link: str, index: int, category: str, messages: Enum = ...,
        metadata: dict[str, Any] = {}, api_link: str = None
    ) -> None:
        super().__init__(link, index, category, messages, metadata, api_link)
        self.messages = CobasiMessages

    async def get_prices (self, page: Page):
        results = []

        await page.route("**/*", lambda route: route.abort()
            if route.request.resource_type == "image"
            else route.continue_()
        )

        max_pages = 100
        last = None

        api_link = (
            "https://mid-back.cobasi.com.br/search/products?hotsite=menu-de-promocoes"
            "&sortby=relevance&resultsperpage=2000&name=menu-de-promocoes&page={}&apikey=cobasi"
        )

        try:
            for page in range(max_pages):
                response = requests.get(api_link.format(page))
                response = response.json()

                if last is None:
                    raw_last = response.get("pagination", {}).get("last", "page=20")
                    pattern = r"&page=(\d+)"

                    re_result = re.findall(pattern, raw_last)
                    if len(re_result) == 0:
                        last = 20
                    else:
                        last = int(re_result[0])

                if page >= last:
                    break

                for offer in response["products"]:
                    extras = {}

                    if offer["status"] != "AVAILABLE":
                        continue

                    name = offer["name"]
                    details = ", ".join(sku["specs"]["default"][0] for sku in offer["skus"])

                    price = offer["price"]
                    old_price = offer["oldPrice"]
                    extras["sub_price"] = self.format_money(offer["subscriptionPrice"])

                    if None in (price, old_price):
                        continue

                    # BUG Fixed to url without https://
                    img = "https:" + offer["images"]["default"]
                    url = "https:" + offer["url"]

                    results.append(
                        self.new_product(name, price, url, details, old_price, img, extras)
                    )

            return results

        except Exception as exc:
            logging.error(traceback.format_exc())
            logging.error(f"Invalid response: {exc}")

        return results


if __name__ == "__main__":
    ready_pages = [ Cobasi(
        link="https://www.cobasi.com.br/promocoes", index=0,
        category="eletronics"
    ) ]
    results = asyncio.run(base.BotBase(ready_pages, True).run())


    print(results)
