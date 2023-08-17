from base import Bot


class Terabyte(Bot):
    # Funcionando
    async def get_prices(self, **kwargs):
        page = self.page
        await page.goto(kwargs.get("link"))
        all_results = []

        await page.wait_for_selector("div.col-xs-12.col-sm-12.col-md-12.nopadding")

        products = await page.query_selector_all(".pbox")
        for product in products:
            if not (await product.query_selector(".prod-new-price")):
                continue

            name_and_details = await product.inner_html()
            name = name_and_details.split(",")[0].strip()
            details = name_and_details.split("\n")[0].strip()

            price = (
                await (await product.query_selector(".prod-new-price")).inner_text()
            ).split(" ")[1]

            obj_old_price = (await (await product.query_selector(".prod-old-price")).inner_text())
            old_price = None
            if obj_old_price:
                old_price = obj_old_price.split(" ")[2]

            url = await (
                await product.query_selector(".commerce_columns_item_image")
            ).get_attribute("href")

            img = await (await product.query_selector("img")).get_attribute("src")

            all_results.append(self.new_product(name, price, url, details, old_price, img))

        return all_results


if __name__ == "__main__":
    bot = Terabyte()
    import asyncio
    results = asyncio.run(
        bot.run(headless=True, link="https://www.terabyteshop.com.br")
    )
    print(results)
