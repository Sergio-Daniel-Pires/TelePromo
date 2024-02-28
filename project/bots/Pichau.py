import asyncio
import json
from enum import Enum
from typing import Any

import requests
from playwright.async_api import Page

try:
    from project.bots import base
except Exception:
    import base

class PichauMessages(str, Enum):
    ALL_TAGS_MATCHED = (
        "*{brand}*: OFERTA PRA VOCÊ! 😱😱\n"
        "\n"
        "🔥🔥🔥 {name}, {details}\n"
        "{condition}"
        "{warranty}"
        "\n"
        "Preço 💵\n"
        "R$ {price:.2f} {installment}"
        "\n"
        "{shipping}"
        "\n"
    )

    AVG_LOW = (
        "*{brand}*: Baixou de preco!\n"
        "\n"
        "🔥🔥 {name}, {details}\n"
        "{condition}"
        "{warranty}"
        "\n"
        "Preço 💵\n"
        "R$ {price:.2f} {installment}"
        "Hist.: {avg}\n"                     # AVG Price
        "\n"
        "{shipping}"
        "\n"
    )

    MATCHED_OFFER = (
        "*{brand}*: Você também pode gostar!\n"
        "\n"
        "🔥 {name}, {details}\n"
        "{condition}"
        "{warranty}"
        "\n"
        "Preço 💵\n"
        "R$ {price:.2f} {installment}"
        "\n"
        "{shipping}"
        "\n"
    )

class Pichau (base.BotRunner):
    messages: Enum = PichauMessages

    def __init__(
        self, link: str, index: int, category: str, messages: Enum = ...,
        metadata: dict[str, Any] = {}, api_link: str = None
    ) -> None:
        super().__init__(link, index, category, messages, metadata, api_link)
        self.messages = PichauMessages

    async def get_prices (self, page: Page):
        return []

    async def get_prices_from_api(self):
        results = []
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            "(KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36"
        )

        for page_num in range(1, 5):
            query = (
                'query promotion {'
                'products('
                    'pageSize: "200" currentPage: "' + str(page_num) + '"'
                    'filter: {price: {from: 0.02 to: 10000}} sort: {price: ASC}'
                ') {'
                'items {'
                    'id url_key name is_openbox openbox_state caracteristicas special_price '
                    'pichau_prices { '
                        'avista avista_discount avista_method base_price final_price '
                        'max_installments min_installment_price'
                    '}'
                    'garantia image { url url_listing } amasty_label { name product_labels { label } }'
                    'mysales_promotion { promotion_name promotion_url }'
                    'stock_status'
                '}}}'
            )
            result = requests.get(self.api_link.format(query), headers={"User-Agent": user_agent}).text
            json_loaded = json.loads(result)

            for product in json_loaded["data"]["products"]["items"]:
                if product.get("stock_status", "OUT_OF_STOCK") == "OUT_OF_STOCK":
                    continue

                extras = { "condition": "", "shipping": "Consulte o Frete" }
                name = product["name"]
                name, details = name.split(",", maxsplit=1) if "," in name else (name, "")
                url = "https://pichau.com.br/" + product["url_key"]
                img = product["image"]["url"]

                if product["is_openbox"]:
                    extras["condition"] = f"\nusado - {product['openbox_state']}\n"

                price = product["pichau_prices"]["avista"]
                old_price = product["pichau_prices"]["base_price"]

                installment = product["pichau_prices"]["final_price"]
                max_installment = product["pichau_prices"]["max_installments"]

                extras["installment"] = f"ou R$ {installment} em {max_installment}x!"

                warranty = product["garantia"]
                if warranty is not None:
                    extras["warranty"] = f'\n(Garantia: {warranty})\n'

                shipping_label = product.get("amasty_label", None)

                if shipping_label is not None:
                    product_labels = shipping_label.get("product_labels", None)
                    if product_labels is not None and isinstance(product_labels, list):
                        extras["shipping"] = product_labels[0]["label"]

                results.append(
                    self.new_product(name, price, url, details, old_price, img, extras)
                )

        return results

if __name__ == "__main__":
    ready_pages = [ Pichau(
        link="https://www.pichau.com.br", index=0, category="eletronics",
        api_link="https://www.pichau.com.br/api/pichau?query={}"
    ) ]
    results = asyncio.run(base.BotBase(ready_pages, True).run())
    print(results)
