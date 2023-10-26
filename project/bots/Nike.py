import asyncio
import json

from playwright.async_api import Page

try:
    from project.bots import base
except Exception:
    import base

class Nike (base.BotRunner):
    # Funcionando
    async def get_prices (self, page: Page):
        results = []

        await page.goto(self.link)

        raw_json = await (await page.query_selector("pre")).inner_text()
        loaded_json = json.loads(raw_json)
        queries = loaded_json["pageProps"]["dehydratedState"]["queries"]

        for query in queries:
            pages = query["state"]["data"]["pages"]

            for page in pages:
                products = page["products"]

                for product in products:
                    if product["status"] != "available":
                        continue

                    name = product["name"]
                    details = name
                    pid = product["id"]
                    img = f"https://imgnike-a.akamaihd.net/480x480/{pid}.jpg"
                    price = product["price"]
                    old_price = product["oldPrice"]
                    url = "https://www.nike.com.br" + product["url"]

                    results.append(self.new_product(name, price, url, details, old_price, img))

        return results

if __name__ == "__main__":
    ready_pages = [ Nike(
        link="https://www.nike.com.br/_next/data/v10-287-1/nav/ofertas/emoferta.json", index=0,
        category="clothes"
    ) ]
    results = asyncio.run(base.BotBase(ready_pages, False).run())
    print(results)
