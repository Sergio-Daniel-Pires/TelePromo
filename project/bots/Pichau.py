import asyncio
import logging
from playwright.async_api import Page

try:
    from project.bots import base
except Exception:
    import base


class Pichau (base.BotRunner):
    # Funcionando
    async def get_prices (self, page: Page):
        results = []
        await page.route("**/*", lambda route: route.abort()
            if route.request.resource_type == "image"
            else route.continue_()
        )
        #page.on("console", lambda msg: print(f"error: {msg.text}") if msg.type == "error" else None)

        await page.goto(self.link, timeout=0, wait_until="domcontentloaded")

        await page.evaluate("window.scrollTo(0, document.body.scrollHeight * .2);")

        try:
            # BUG nao visivel
            await page.wait_for_selector("a[data-cy='list-product']")
        except Exception as exc:
            await page.screenshot(path="Pichau.jpg")

            raise exc

        await self.scroll_to_bottom(page, wait_before_roll=0.3)

        second_section = (await page.query_selector_all("section"))[1]

        all_products = await second_section.query_selector_all("a[data-cy='list-product']")

        for product_selector in all_products:
            name_and_details = (await (
                await product_selector.query_selector("h2")
            ).inner_text()).split(",", 1)
            name = details = name_and_details[0]
            if len(name_and_details) > 1:
                details = name_and_details[1]

            price = None
            obj_price = (
                await product_selector.query_selector(".MuiCardContent-root > div :nth-child(3)")
            )
            if obj_price:
                price = await obj_price.inner_text()

            old_price = None
            obj_old_price = await product_selector.query_selector(
                ".MuiCardContent-root > div :nth-child(1) > div > div > s"
            )

            if obj_old_price:
                old_price = await obj_old_price.inner_text()

            if old_price is not None and price is None:
                price = old_price

            elif old_price is None and price is not None:
                old_price = price

            if None in (price, old_price):
                continue

            url = await product_selector.get_attribute("href")

            img_selector = await product_selector.query_selector("img")

            if img_selector:
                img = await (img_selector).get_attribute("src")
            else:
                img = None

            logging.debug(__class__, old_price, price)
            results.append(
                self.new_product(name, price, url, details, old_price, img)
            )

        return results


if __name__ == "__main__":
    ready_pages = [ Pichau(
        link="https://www.pichau.com.br", index=0,
        category="eletronics"
    ) ]
    scrapper = base.BotBase(ready_pages, True)
    results = asyncio.run(scrapper.run())
    print(results[0].results)
