from .base import Bot


class Nike (Bot):
    # Funcionando
    async def get_prices (self, **kwargs):
        page = self.page
        await page.goto(kwargs.get("link"))
        all_results = []

        await page.wait_for_selector("div.bPRNCw")

        products = await page.query_selector_all("div.bPRNCw")
        for product in products:
            name = await (await product.query_selector("div > p:nth-child(1)")).inner_text()
            details = name

            prices = await product.query_selector_all("div.jTWwgZ > p")
            if len(prices) == 0:
                continue

            price = await prices[0].inner_text()

            if len(prices) > 1:
                old_price = await prices[1].inner_text()

            url = await (
                await product.query_selector("a")
            ).get_attribute("href")

            img = await (await product.query_selector("img")).get_attribute("src")

            print(img)
            print(url)
            all_results.append(self.new_product(name, price, url, details, old_price, img))

        return all_results


if __name__ == "__main__":
    bot = Nike()
    import asyncio
    results = asyncio.run(
        bot.run(headless=True, link="https://www.nike.com.br/nav/ofertas/emoferta")
    )
    print(results)
