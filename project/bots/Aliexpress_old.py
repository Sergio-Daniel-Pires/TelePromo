import logging
import re
import traceback

import requests

try:
    from project.bots.base import Bot
except Exception:
    from base import Bot

def get_shipping_type (html_text: str) -> str:
    re_pattern = r'Frete (grátis)|\+ envio: R\$(\d*,\d*)'

    found = re.search(re_pattern, html_text)
    if len(found) == 0:
        return None

    return found[0][1]

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

        await self.scroll_to_bottom(rolls=10)

        products = await page.query_selector_all("a.search-card-item")

        for product_obj in products:
            name = await (
                await product_obj.query_selector("div > h1")
            ).inner_text()

            details = name
            splitted_name = name.split(",", 1)

            if len(splitted_name) > 1:
                name = splitted_name[0]
                details = splitted_name[1]

            prices = await product_obj.query_selector("div:nth-of-type(2) > div:nth-child(1)")

            if not prices:
                continue

            list_prices = (await prices.inner_text()).split("\n")
            price = list_prices[0]
            old_price = price

            if len(list_prices) > 1:
                old_price = list_prices[1]

            url = await (
                await product_obj.query_selector("a")
            ).get_attribute("href")

            img = await (await product_obj.query_selector("img")).get_attribute("src")

            url = f"https:{await product_obj.get_attribute('href')}"
            img = (
                "https:" +
                await (await product_obj.query_selector("img")).get_attribute("src")
            )

            infos = await product_obj.query_selector("div:nth-of-type(2)")
            shipping = get_shipping_type(await infos.inner_html())

            results.append(
                self.new_product(name, price, url, details, old_price, img, shipping)
            )

            if len(results) == 10:
                break

        return results


if __name__ == "__main__":
    bot = Aliexpress()
    import asyncio
    results = asyncio.run(
        bot.run(
            headless=False,
            link="https://pt.aliexpress.com/category/201001900/"
                 "women-clothing.html?CatId=201001900&g=y"
        )
    )
    print(results)
