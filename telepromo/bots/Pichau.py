from base import Bot

import time

class Pichau(Bot):
    """
    Erros:
    Carrosel carrega nunk   
    """

    async def scroll_to_bottom(self, page) -> None:
        for i in range(8):
            await page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * .{i//2 + 5});"),
            await asyncio.sleep(0.3)

    async def get_prices(self, **kwargs):
        page = self.page
        
        page.on("console", lambda msg: print(f"error: {msg.text}") if msg.type == "error" else None)
        
        await page.goto(kwargs.get('link'), timeout=0, wait_until="domcontentloaded")
        all_results = []

        await page.evaluate("window.scrollTo(0, document.body.scrollHeight * .2);")
        
        try:
            await page.wait_for_selector("a[data-cy='list-product']")
        except Exception as exc:
            await page.screenshot(path="Pichau.jpg")
            
            raise exc
        
        await self.scroll_to_bottom(page)

        second_section = (await page.query_selector_all("section"))[1]
        for product_selector in (await second_section.query_selector_all('a[data-cy="list-product"]')):
            name = await (
                await product_selector.query_selector('h2')
            ).inner_text()
            
            price = await (
                await product_selector.query_selector('.MuiCardContent-root > div :nth-child(3)')
            ).inner_text()
            price = float((price[3:].replace('.', '')).replace(',', '.'))
            
            old_price = await (
                await product_selector.query_selector('.MuiCardContent-root > div :nth-child(1) > div > div > s')
            ).inner_text()
            old_price = float((old_price[3:].replace('.', '')).replace(',', '.'))
            
            url = await product_selector.get_attribute("href")

            img_selector = await product_selector.query_selector('img')

            if img_selector:
                img = await (img_selector).get_attribute("src")
            else:
                img = None

            all_results.append(
                {
                    "name": name, "details": name, "price": price, "oldPrice": old_price,
                    "url": url, "img": img
                }
            )

        return all_results

if __name__ == "__main__":
    bot = Pichau()
    import asyncio
    results = asyncio.run(
        bot.run(headless=True, link="https://www.pichau.com.br")
    )
    print(results)
