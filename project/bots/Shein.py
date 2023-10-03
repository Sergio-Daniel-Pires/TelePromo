import asyncio

try:
    from project.bots.base import Bot
except Exception:
    from base import Bot

import json

class Shein (Bot):
    # Corrigir prices
    async def get_prices (self, **kwargs):
        page = self.page
        await page.goto(kwargs.get("link"), timeout=12000)
        all_results = []

        try:
            await page.wait_for_selector("div.glass-product-card__assets", timeout=1000)
        except Exception:
            await page.screenshot(path="teste.jpg", full_page=True)
            raise Exception("")

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

            all_results.append(self.new_product(name, price, url, details, old_price, img))

        return all_results


if __name__ == "__main__":
    bot = Shein()
    results = asyncio.run(
        bot.run(
            headless=True,
            link=("https://m.shein.com/br/new/WHATS-NEW-sc-00255950.html")
        )
    )
    print(results)
