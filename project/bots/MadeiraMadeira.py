import logging

from project.bots.base import Bot


class MadeiraMadeira (Bot):
    """
    Erros:
    img nao funciona
    """
    async def get_prices (self, **kwargs):
        page = self.page

        await page.goto(self.link)
        results = []

        await page.wait_for_selector("article")

        products = await page.query_selector_all("article > a")

        for product_obj in products:
            name = await (await product_obj.query_selector("h2")).inner_text()
            details = name

            price = await (await product_obj.query_selector(
                "span.cav--c-gNPphv-hyvuql-weight-bold"
            )).inner_text()

            old_price = price

            obj_old_price = await product_obj.query_selector(
                "span.cav--c-gNPphv.cav--c-gNPphv-iihFNG-size-bodyXSmall"
                ".cav--c-gNPphv-ijymXNu-css"
            )
            if obj_old_price:
                old_price = (await obj_old_price.inner_text())[3:]

            url = await product_obj.get_attribute("href")
            img = await (
                await product_obj.query_selector("img.main-img")
            ).get_attribute("src")

            logging.debug(__class__, old_price, price)
            results.append(
                self.new_product(name, price, url, details, old_price, img)
            )

        return results


if __name__ == "__main__":
    bot = MadeiraMadeira()
    import asyncio
    results = asyncio.run(
        bot.run(
            headless=True, link="https://www.madeiramadeira.com.br/ofertas-do-dia"
        )
    )
    print(results)
