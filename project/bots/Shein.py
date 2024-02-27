import asyncio
from enum import Enum
from typing import Any

from playwright.async_api import Page

try:
    from project.bots import base
    from project.bots.Aliexpress import InternationalMessages

except Exception:
    import base
    from Aliexpress import InternationalMessages

import json


def build_url (url_name: str, id: int, cat_id: int):
    url_name = url_name.replace(" ", "-")
    return f"https://m.shein.com/br/{url_name}-p-{id}-cat-{cat_id}.html"

class Shein (base.BotRunner):
    messages: Enum = InternationalMessages

    def __init__(
        self, link: str, index: int, category: str, messages: Enum = ...,
        metadata: dict[str, Any] = {}, api_link: str = None
    ) -> None:
        super().__init__(link, index, category, messages, metadata, api_link)
        self.messages = InternationalMessages

    # Corrigir prices
    async def get_prices (self, page: Page):
        results = []

        await page.goto(self.link, timeout=30000)
        await self.scroll_to_bottom(page)

        raw_products_json = await page.locator(
            "//script[text()[contains(.,'var _constants')]]"
        ).inner_html()

        products_json = None

        for text in raw_products_json.split("\n"):
            text = text.strip()
            if text.startswith("var _constants"):
                products_json = text.split(" = ")[1]

        if products_json is None:
            return False

        products_json = json.loads(products_json)
        offers = products_json["contextForSSR"]["goods"]

        for offer in offers:
            extras = {}

            name = offer["goods_name"]
            details = name

            img = "https:" + offer["goods_img"]

            price = offer["salePrice"]["amount"]
            old_price = offer["retailPrice"]["amount"]

            url = build_url(offer["goods_url_name"], offer["goods_id"], offer["cat_id"])
            shipping = offer["pretreatInfo"]["mallTagsInfo"]["mall_name"]
            if shipping == "Envio Nacional":
                shipping = "🇧🇷 Ja no Brasil!"
            else:
                shipping = "✈️ Internacional"

            extras = { "shipping": shipping }

            results.append(
                self.new_product(name, price, url, details, old_price, img, extras)
            )

        return results


if __name__ == "__main__":
    ready_pages = [ Shein(
        link="https://m.shein.com/br/new/WHATS-NEW-sc-00255950.html", index=0,
        category="clothes"
    ) ]
    results = asyncio.run(base.BotBase(ready_pages, True).run())


    print(results)
