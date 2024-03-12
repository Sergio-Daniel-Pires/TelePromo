import asyncio
import json

from playwright.async_api import Page

try:
    from project.bots import base
except Exception:
    import base


class Magalu (base.BotRunner):
    async def get_prices (self, page: Page):
        results = []

        async def block (route):
            if route.request.resource_type in ( "image", "stylesheet", "script", "font" ):
                await route.abort()

            else:
                await route.continue_()

        await page.route("**/*", block)

        await page.set_extra_http_headers({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "pt",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-Ch-Ua": '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "Linux",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        })

        await page.goto(self.link, timeout=30000)

        await page.wait_for_selector("script[id=__NEXT_DATA__]", state="attached", timeout=3000)

        raw_json_obj = await (await page.query_selector("script[id=__NEXT_DATA__]")).inner_html()
        response = json.loads(raw_json_obj)

        products = response["props"]["pageProps"]["data"]["search"]["products"]
        for product in products:
            if not product["available"]:
                continue

            extras = {}

            name = product["title"]
            details = product["description"]

            price = product["price"]["bestPrice"]
            original_price = product["price"]["price"]

            img = product["image"].format(w=400, h=400)

            url = f"https://www.magazineluiza.com.br/" + product["path"]

            results.append(
                self.new_product(name, price, url, details, original_price, img, extras)
            )

        return results

    async def get_prices_from_api (self):
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            "(KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36"
        )

        return results

if __name__ == "__main__":
    ready_pages = [ Magalu(
        link="https://www.magazineluiza.com.br/selecao/ofertasdodia/", index=0,
        category="eletronics"
    ) ]
    results = asyncio.run(base.BotBase(ready_pages, True).run())

    print(results)
