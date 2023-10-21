from playwright.async_api import Page

try:
    from project.bots.base import BotRunner
except Exception:
    from base import BotRunner

class Nike (BotRunner):
    # Funcionando
    async def get_prices (self, page: Page):
        results = []

        await page.route("**/*", lambda route: route.abort()
            if route.request.resource_type == "image"
            else route.continue_()
        )

        await page.goto(self.link)

        await page.wait_for_selector("div.bPRNCw")

        products = await page.query_selector_all("div.bPRNCw")
        for product in products:
            name = await (await product.query_selector("div > p:nth-child(1)")).inner_text()
            details = name

            prices = await product.query_selector_all("div.jTWwgZ > p")
            if len(prices) == 0:
                continue

            price = await prices[0].inner_text()
            old_price = price

            if len(prices) > 1:
                old_price = await prices[1].inner_text()

            url = await (
                await product.query_selector("a")
            ).get_attribute("href")

            img = await (await product.query_selector("img")).get_attribute("src")
            if "image/gif;base64," in img:
                img = None

            results.append(self.new_product(name, price, url, details, old_price, img))

        return results


if __name__ == "__main__":
    bot = Nike()
    import asyncio
    results = asyncio.run(
        bot.run(headless=True, link="https://www.nike.com.br/nav/ofertas/emoferta")
    )
    print(results)
