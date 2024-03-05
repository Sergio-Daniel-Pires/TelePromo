import asyncio
import json
import logging

import requests
from playwright.async_api import Page

try:
    from project.bots import base
except Exception:
    import base


class MadeiraMadeira (base.BotRunner):
    """
    Erros:
    img nao funciona
    """
    async def get_prices (self, page: Page):
        results = []
        await page.route("**/*", lambda route: route.abort()
            if route.request.resource_type == "image"
            else route.continue_()
        )

        await page.goto(self.link, timeout=12000)

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

            results.append(
                self.new_product(name, price, url, details, old_price, img)
            )

        return results

    async def get_prices_from_api (self):
        results = []
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            "(KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36"
        )

        api_link = (
            "https://2zx4gyqyq3-dsn.algolia.net/1/indexes/*/queries?"
            "&x-algolia-api-key=1568dbb80ec68fa971ef9edbfb2cfd30&x-algolia-application-id=2ZX4GYQYQ3"
        )

        index_names = [
            "vr-prod-poc-madeira-listings-best-seller-desc", "vr-prod-poc-madeira-recommendation"
        ]

        for index_name in index_names:
            try:
                response = requests.post(
                    api_link, data=json.dumps({"requests": [ { "indexName": index_name} ]}),
                    headers={"User-Agent": user_agent, "Content-Type": "Application/json"},
                ).json()

                for result in response["results"]:
                    for product in result["hits"]:
                        extras = {}

                        name = product["nome"]
                        details = product["descricao"]

                        price = product["preco_por"]
                        old_price = product["preco_de"]

                        img = product["imagens"][0]

                        url = f"https://www.madeiramadeira.com.br" + product["url"]

                        results.append(
                            self.new_product(name, price, url, details, old_price, img, extras)
                        )

            except Exception as exc:
                #logging.error(traceback.format_exc())
                logging.error(f"Invalid response: {exc}")

        return results

if __name__ == "__main__":
    ready_pages = [ MadeiraMadeira(
        link="https://www.madeiramadeira.com.br/ofertas-do-dia", index=0,
        category="house", api_link=""
    ) ]
    results = asyncio.run(base.BotBase(ready_pages, True).run())


    print(results)
