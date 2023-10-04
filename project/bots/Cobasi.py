import asyncio
import logging
import re
import traceback
from enum import Enum
from typing import Any

import requests

try:
    from project.bots.base import Bot
except Exception:
    from base import Bot

class CobasiMessages(str, Enum):
    ALL_TAGS_MATCHED = (
        "*{}*: OFERTA PRA VOCÊ! 🐶😺\n"   # Site name
        "\n"
        "🔥🔥🔥 {}\n"                           # Product name
        "\n"
        "Preço 💵\n"
        "R$ {:.2f}"                          # Price
        "\n"
        "\n"
        "🐶 Amigo Cobasi\n"
        "R$ {:.2f}"                          # Prime price
        "\n"
    )

    AVG_LOW = (
        "*{}*: Baixou de preco!\n"        # Site name
        "\n"
        "🔥🔥 {}\n"                       # Product name
        "Preço 💵\n"
        "\n"
        "R$ {:.2f}\n"                  # Price
        "Hist.: {}\n"                     # AVG Price
        "\n"
        "\n"
        "🐶 Amigo Cobasi\n"
        "R$ {:.2f}"                    # Prime price
        "\n"
    )

    MATCHED_OFFER = (
        "*{}*: Recomendado pro seu Pet!\n"    # Site name
        "\n"
        "🔥 {}\n"                        # Product name
        "Preço 💵\n"
        "R$ {:.2f}"                   # Price
        "\n"
        "\n"
        "🐶 Amigo Cobasi\n"
        "R$ {:.2f}"                   # Prime price
        "\n"
    )

class Cobasi (Bot):
    async def get_prices (self, **kwargs):
        page = self.page

        max_pages = 100
        last = None

        results = []

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
                        self.new_product(
                            name, price, url, details, old_price, img, extras
                        )
                    )

            return results

        except Exception as exc:
            logging.error(traceback.format_exc())
            logging.error(f"Invalid response: {exc}")

        return results

    def promo_message (
        self, result: dict[str, Any], avarage: float, prct_equal: float
    ):
        brand = result["brand"]
        product_name = result["name"]
        details = result["details"].strip()
        price = result["price"]
        url = result["url"]
        img = result["img"]

        prime_price = result["extras"].get("sub_price", price)

        if product_name == details:
            details = ""

        product_desc = f"{product_name}, {details}"

        if prct_equal == 1:
            message = CobasiMessages.ALL_TAGS_MATCHED.format(
                brand, product_desc, price, prime_price, img, url
            )

        elif price < avarage:
            message = CobasiMessages.AVG_LOW.format(
                brand, product_desc, price, avarage, prime_price, img, url
            )

        else:
            message = CobasiMessages.MATCHED_OFFER.format(
                brand, product_desc, price, prime_price, img, url
            )

        return message


if __name__ == "__main__":
    bot = Cobasi()
    results = asyncio.run(
        bot.run(headless=True, link="https://www.cobasi.com.br/promocoes")
    )
    print(results)
