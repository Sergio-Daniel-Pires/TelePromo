from base import Bot


class Kabum(Bot):
    async def get_prices (self, **kwargs):
        page = self.page

        await page.goto(self.link)
        results = []

        await page.wait_for_selector("section#blocoProdutosListagem")

        products = await page.query_selector_all("div.productCard")

        for product_obj in products:
            name_and_details = await (await product_obj.query_selector(".nameCard")).inner_text()
            name, details = name_and_details.split(",", 1)

            price = await (await product_obj.query_selector(".priceCard")).inner_text()
            old_price = await (await product_obj.query_selector(".oldPriceCard")).inner_text()

            url = await (await product_obj.query_selector(".productLink")).get_attribute("href")
            img = await (await product_obj.query_selector(".imageCard")).get_attribute("src")

            results.append(
                self.new_product(name, price, url, details, old_price, img)
            )

        return results


if __name__ == "__main__":
    bot = Kabum()
    import asyncio
    results = asyncio.run(
        bot.run(headless=True, link="https://www.kabum.com.br/ofertas/BLACKNINJA")
    )
    print(results)
