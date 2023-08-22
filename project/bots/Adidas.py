import logging

from project.bots.base import Bot


class Adidas (Bot):
    # Funcionando
    async def get_prices (self, **kwargs):
        page = self.page
        await page.goto(kwargs.get("link"))
        all_results = []

        try:
            await page.wait_for_selector("div.glass-product-card__assets")
        except Exception:
            await page.screenshot(path="teste.jpg", full_page=True)
            raise Exception("")

        products = await page.query_selector_all("div.glass-product-card")
        for product in products:
            name = await (await product.query_selector("p.glass-product-card__title")).inner_text()
            details = name

            obj_prices = await product.query_selector_all("div.gl-price-item")
            price = (await obj_prices[0].inner_text())
            old_price = (await obj_prices[1].inner_text())

            url = await (
                await product.query_selector("a.glass-product-card__assets-link")
            ).get_attribute("href")

            img = await (await product.query_selector("img")).get_attribute("src")

            logging.debug(__class__, old_price, price)
            all_results.append(self.new_product(name, price, url, details, old_price, img))
            break

        return all_results


if __name__ == "__main__":
    bot = Adidas()
    import asyncio
    results = asyncio.run(
        bot.run(headless=True, link="https://www.adidas.com.br/flash_sale")
    )
    print(results)