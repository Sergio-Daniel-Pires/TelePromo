import asyncio
from enum import Enum
from typing import Any

try:
    from project.bots.base import Bot
except Exception:
    from base import Bot

import json


class InternationalMessages(str, Enum):
    ALL_TAGS_MATCHED = (
        "*{}*: SUPER OFERTA PRA VOCE! 😱😱\n"   # Site name
        "\n"
        "🔥🔥🔥 {}\n"                           # Product name
        "{}\n"                                  # Frete
        "\n"
        "R$ {:.2f} 💵"                          # Price
        "\n"
    )

    AVG_LOW = (
        "*{}*: Baixou de preco!\n"        # Site name
        "\n"
        "🔥🔥 {}\n"                       # Product name
        "{}\n"                            # Frete
        "\n"
        "R$ {:.2f} 💵\n"                  # Price
        "Hist.: {}\n"                     # AVG Price
        "\n"
    )

    MATCHED_OFFER = (
        "*{}*: Você também pode gostar!\n"    # Site name
        "\n"
        "🔥 {}\n"                             # Product name
        "{}\n"                                # Frete
        "\n"
        "R$ {:.2f} 💵"                        # Price
        "\n"
    )

class Aliexpress (Bot):
    async def try_reload_aliexpress (self):
        items = asyncio.create_task(
            self.page.wait_for_selector("a.search-card-item"), name="grid_items"
        )

        wrong_line = asyncio.create_task(
            self.page.wait_for_selector("span.comet-icon"), name="wrong"
        )
        correct = False

        for _ in range(3):
            _, _ = await asyncio.wait(
                (items, wrong_line),
                return_when=asyncio.FIRST_COMPLETED
            )
            if items.done():
                wrong_line.cancel()
                correct = True
                break

            else:
                await self.page.reload()

        if not correct:
            raise Exception("Impossible to load grid items")

    async def get_prices (self, **kwargs):
        page = self.page

        results = []

        await page.goto(self.link, timeout=30000)

        await self.try_reload_aliexpress()

        raw_products_json = await page.locator(
            "//script[text()[contains(.,'window._dida_config_._init_data_=')]]"
        ).inner_html()

        raw_products_json = raw_products_json.split("\n")[1]
        raw_products_json = raw_products_json[42:-2]
        products_json = json.loads(raw_products_json)
        products_data = products_json["data"]["root"]["fields"]["mods"]["itemList"]

        for product_obj in products_data["content"]:
            extras = {}
            product_id = product_obj["productId"]

            name = product_obj["title"]["seoTitle"]
            details = None

            url = f"https://pt.aliexpress.com/item/{product_id}.html"

            img = "https://" + product_obj["image"]["imgUrl"][2:]

            for selling_point in product_obj.get("sellingPoints", []):
                if "shipping" in selling_point["source"]:
                    extras["shipping"] = selling_point["tagContent"]["tagText"]

            prices = product_obj["prices"]

            price = prices["salePrice"]["minPrice"]
            old_price = price

            original_price = prices.get("originalPrice", None)
            if original_price:
                old_price = original_price["minPrice"]

            results.append(
                self.new_product(name, price, url, details, old_price, img, extras)
            )

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
        shipping = result.get("shipping", "Consulte o Frete!")

        if product_name == details:
            details = ""

        product_desc = f"{product_name}, {details}"

        if prct_equal == 1:
            message = InternationalMessages.ALL_TAGS_MATCHED.format(
                brand, product_desc, shipping, price, img, url
            )

        elif price < avarage:
            message = InternationalMessages.AVG_LOW.format(
                brand, product_desc, shipping, price, avarage, img, url
            )

        else:
            message = InternationalMessages.MATCHED_OFFER.format(
                brand, product_desc, shipping, price, img, url
            )

        return message


if __name__ == "__main__":
    bot = Aliexpress()
    results = asyncio.run(
        bot.run(
            headless=False,
            link=(
                "https://pt.aliexpress.com/category/201000054/"
                "cellphones-telecommunications.html"
            )
        )
    )
    print(results)
