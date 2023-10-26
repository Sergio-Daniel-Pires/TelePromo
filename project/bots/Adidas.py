import asyncio
import json
from enum import Enum
from typing import Any

from playwright.async_api import Page

try:
    from project.bots import base
except Exception:
    import base

class AdidasMessages(str, Enum):
    ALL_TAGS_MATCHED = (
        "*{brand}*: OFERTA PRA VOCÊ!\n"   # Site name
        "\n"
        "🔥🔥🔥 {name}\n"                           # Product name
        "\n"
        "Disponiveis:📏\n"
        "{sizes}\n"
        "\n"
        "Preço 💵\n"
        "R$ {price:.2f}"                          # Price
        "\n"
    )

    AVG_LOW = (
        "*{brand}*: Baixou de preco!\n"        # Site name
        "\n"
        "🔥🔥 {name}\n"                       # Product name
        "\n"
        "Disponiveis:📏\n"
        "{sizes}\n"
        "\n"
        "Preço 💵\n"
        "\n"
        "R$ {price:.2f}\n"                  # Price
        "Hist.: {avg}\n"                     # AVG Price
        "\n"
    )

    MATCHED_OFFER = (
        "*{brand}*: Você também pode gostar!\n"    # Site name
        "\n"
        "🔥 {name}\n"                        # Product name
        "\n"
        "Disponiveis:📏\n"
        "{sizes}\n"
        "\n"
        "Preço 💵\n"
        "R$ {price:.2f}"                   # Price
        "\n"
    )

class Adidas (base.BotRunner):
    messages: Enum = AdidasMessages

    def __init__(
        self, link: str, index: int, category: str, messages: Enum = ...,
        metadata: dict[str, Any] = {}, api_link: str = None
    ) -> None:
        super().__init__(link, index, category, messages, metadata, api_link)
        self.messages = AdidasMessages

    async def get_prices (self, page: Page):
        results = []

        await page.route("**/*", lambda route: route.abort()
            if route.request.resource_type == "image"
            else route.continue_()
        )

        await page.goto(self.link, timeout=12000)

        raw_json = await (await page.query_selector("pre")).inner_text()
        loaded_json = json.loads(raw_json)

        products = loaded_json["raw"]["itemList"]["items"]
        for product in products:
            extras = { "sizes": "" }

            url = "https://www.adidas.com.br" + product["link"]
            name = product["altText"]
            img = product["image"]["src"]
            price = product["salePrice"]
            old_price = product["price"]

            # Extras
            extras["sizes"] = ", ".join(
                [size for size in product["availableSizes"] if size != "hidden"]
            )
            shipping = product.get("customBadge", "")
            extras["shipping"] = shipping if "frete" in shipping.lower() else "Consulte o frete!"

            results.append(
                self.new_product(name, price, url, name, old_price, img, extras)
            )

        return results


if __name__ == "__main__":
    ready_pages = [ Adidas(
        link="https://www.adidas.com.br/api/plp/content-engine?query=flash_sale", index=0, category="clothes"
    ) ]
    results = asyncio.run(base.BotBase(ready_pages, True).run())


    print(results)
