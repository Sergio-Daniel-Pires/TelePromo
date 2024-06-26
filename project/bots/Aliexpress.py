import asyncio
from enum import Enum

from playwright.async_api import Page

try:
    from project.bots import base

except Exception:
    import base

import json


class InternationalMessages(str, Enum):
    ALL_TAGS_MATCHED = (
        "*{brand}*: SUPER OFERTA PRA VOCE! 😱😱\n"   # Site name
        "\n"
        "🔥🔥🔥 {name}\n"                           # Product name
        "{shipping}\n"                                  # Frete
        "\n"
        "R$ {price:.2f} 💵"                          # Price
        "\n"
    )

    AVG_LOW = (
        "*{brand}*: Baixou de preco!\n"        # Site name
        "\n"
        "🔥🔥 {name}\n"                       # Product name
        "{shipping}\n"                            # Frete
        "\n"
        "R$ {price:.2f} 💵\n"                  # Price
        "Hist.: {avg}\n"                     # AVG Price
        "\n"
    )

    MATCHED_OFFER = (
        "*{brand}*: Você também pode gostar!\n"    # Site name
        "\n"
        "🔥 {name}\n"                             # Product name
        "{shipping}\n"                                # Frete
        "\n"
        "R$ {price:.2f} 💵"                        # Price
        "\n"
    )

class Aliexpress (base.BotRunner):
    messages: Enum = InternationalMessages

    async def get_prices (self, page: Page):
        results = []

        await page.route("**/*", lambda route: route.abort()
            if route.request.resource_type == "image"
            else route.continue_()
        )

        await page.goto(self.link, timeout=30000)

        await self.try_reload_aliexpress(page)

        raw_products_json = await page.locator(
            "//script[text()[contains(.,'window._dida_config_._init_data_=')]]"
        ).inner_html()

        raw_products_json = raw_products_json.split("\n")[1]
        raw_products_json = raw_products_json[42:-2]
        products_json = json.loads(raw_products_json)
        products_data = products_json["data"]["root"]["fields"]["mods"]["itemList"]

        for product_obj in products_data["content"]:
            product_id = product_obj["productId"]

            name = product_obj["title"]["seoTitle"]
            details = None

            url = f"https://pt.aliexpress.com/item/{product_id}.html"

            img = "https://" + product_obj["image"]["imgUrl"][2:]

            shipping = "Consulte o frete!"
            for selling_point in product_obj.get("sellingPoints", []):
                if "shipping" in selling_point["source"]:
                    shipping = selling_point["tagContent"]["tagText"]
                    break

            extras = { "shipping": shipping }

            prices = product_obj["prices"]

            price = prices["salePrice"]["minPrice"]
            original_price = price

            if prices.get("originalPrice", None):
                original_price = prices["originalPrice"]["minPrice"]

            results.append(self.new_product(name, price, url, details, original_price, img, extras))

        return results

    async def try_reload_aliexpress (self, page: Page):
        items = asyncio.create_task(
            page.wait_for_selector("a.search-card-item"), name="grid_items"
        )

        wrong_line = asyncio.create_task(
            page.wait_for_selector("span.comet-icon"), name="wrong"
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
                await page.reload()

        if not correct:
            raise Exception("Impossible to load grid items")

if __name__ == "__main__":
    ready_pages = [ Aliexpress(
        link="https://pt.aliexpress.com/category/201000054/cellphones-telecommunications.html",
        index=0, category="eletronics"
    ) ]
    results = asyncio.run(base.BotBase(ready_pages, True).run())


    print(results)
