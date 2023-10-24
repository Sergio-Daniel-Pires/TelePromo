import logging

from playwright.async_api import Page

try:
    from project.bots.base import BotRunner
except Exception:
    from base import BotRunner

class Adidas (BotRunner):
    async def get_prices (self, page: Page):
        results = []

        await page.route("**/*", lambda route: route.abort()
            if route.request.resource_type == "image"
            else route.continue_()
        )

        await page.goto(self.link, timeout=12000)

        await page.wait_for_selector("div.glass-product-card__assets", timeout=1000)

        products = await page.query_selector_all("div.glass-product-card")

        for product in products:
            name = await (await product.query_selector("p.glass-product-card__title")).inner_text()
            details = name

            obj_prices = await product.query_selector_all("div.gl-price-item")
            if obj_prices == []:
                continue

            price = (await obj_prices[0].inner_text())
            old_price = (await obj_prices[1].inner_text())

            url = await (
                await product.query_selector("a.glass-product-card__assets-link")
            ).get_attribute("href")

            img = await (await product.query_selector("img")).get_attribute("src")

            results.append(self.new_product(name, price, url, details, old_price, img))

        return results


if __name__ == "__main__":
    bot = Adidas()
    import asyncio
    results = asyncio.run(
        bot.run(headless=True, link="https://www.adidas.com.br/flash_sale")
    )
    print(results)
