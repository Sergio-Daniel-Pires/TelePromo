import asyncio

try:
    from project.bots.base import Bot
except Exception:
    from base import Bot

import json

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

        await page.goto(self.link)

        await self.try_reload_aliexpress()

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

            shipping = None
            for selling_point in product_obj.get("sellingPoints", []):
                if "shipping" in selling_point["source"]:
                    shipping = selling_point["tagContent"]["tagText"]

            prices = product_obj["prices"]

            price = prices["salePrice"]["minPrice"]
            old_price = price

            original_price = prices.get("originalPrice", None)
            if original_price:
                old_price = original_price["minPrice"]

            results.append(
                self.new_product(name, price, url, details, old_price, img, shipping)
            )

        return results


if __name__ == "__main__":
    bot = Aliexpress()
    results = asyncio.run(
        bot.run(
            headless=True,
            link=(
                "https://pt.aliexpress.com/category/201000054/"
                "cellphones-telecommunications.html"
            )
        )
    )
    print(results)
