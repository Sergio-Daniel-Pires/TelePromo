import asyncio
import logging

from playwright.async_api import Page

try:
    from project.bots import base
except Exception:
    import base

class Terabyte (base.BotRunner):
    # Funcionando
    async def get_prices (self, page: Page):
        results = []

        await page.route("**/*", lambda route: route.abort()
            if route.request.resource_type == "image"
            else route.continue_()
        )
        await page.goto(self.link)

        try:
            # BUG nao visivel
            await page.wait_for_selector("div.col-xs-12.col-sm-12.col-md-12.nopadding")
        except Exception as exc:
            await page.screenshot(path="Terabyte.jpg")

        products = await page.query_selector_all(".pbox")
        for product in products:
            if not (await product.query_selector(".prod-new-price")):
                continue

            name_and_details = await product.inner_text()
            name = name_and_details.split(",")[0].strip()
            details = name_and_details.split("\n")[0].strip()

            price = (
                await (await product.query_selector(".prod-new-price")).inner_text()
            ).split(" ")[1]

            obj_old_price = (await (await product.query_selector(".prod-old-price")).inner_text())
            old_price = price
            if obj_old_price:
                old_price = obj_old_price.split(" ")[2]

            url = await (
                await product.query_selector(".commerce_columns_item_image")
            ).get_attribute("href")

            img = await (await product.query_selector("img")).get_attribute("src")

            results.append(self.new_product(name, price, url, details, old_price, img))

        return results


if __name__ == "__main__":
    ready_pages = [ Terabyte(
        link="https://www.terabyteshop.com.br/promocoes", index=0,
        category="eletronics"
    ) ]
    scrapper = base.BotBase(ready_pages, True)
    results = asyncio.run(scrapper.run())
    print(results)
