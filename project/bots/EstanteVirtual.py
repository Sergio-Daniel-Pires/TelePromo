import asyncio
import requests
from enum import Enum
from typing import Any

from playwright.async_api import Page

try:
    from project.bots import base
except Exception:
    import base

class EstanteVirtualMessages(str, Enum):
    ALL_TAGS_MATCHED = (
        "*{brand}*: OFERTA PRA VOCÊ! 📚😱\n"
        "\n"
        "🔥🔥🔥 {name}\n"
        "{author}"
        "{details}"
        "\n"
        "Preço 💵\n"
        "R$ {price:.2f}"
        "\n"
        "{shipping}"
        "{sent_from}"
        "\n"
    )

    AVG_LOW = (
        "*{brand}*: Baixou de preco!\n"
        "\n"
        "🔥🔥 {name}\n"
        "{author}"
        "{details}"
        "\n"
        "Preço 💵\n"
        "R$ {price:.2f}"
        "Hist.: {avg}\n"                     # AVG Price
        "\n"
        "{shipping}"
        "{sent_from}"
        "\n"
    )

    MATCHED_OFFER = (
        "*{brand}*: Você também pode gostar!\n"
        "\n"
        "🔥 {name}\n"
        "{author}"
        "{details}"
        "\n"
        "Preço 💵\n"
        "R$ {price:.2f}"
        "\n"
        "{shipping}"
        "{sent_from}"
        "\n"
    )

class EstanteVirtual (base.BotRunner):
    messages: Enum = EstanteVirtualMessages

    def __init__(
        self, link: str, index: int, category: str, messages: Enum = ...,
        metadata: dict[str, Any] = {}, api_link: str = None
    ) -> None:
        super().__init__(link, index, category, messages, metadata, api_link)
        self.messages = EstanteVirtualMessages

    async def get_prices (self, page: Page):
        """
        Infelizmente para o Estante Virtual, não existe bot bom o suficiente
        que faça ele rodar sem ser direto via API :/
        """
        return []

    async def get_prices_from_api(self):
        all_ids = set()
        results = []

        queries = (
            "mais_vendidos", "listagem?desconto_max=5", "listagem?desconto_max=10",
            "listagem?desconto_max=15", "listagem?desconto_max=20", "listagem?desconto_max=25",
            "listagem?desconto_max=30"
        )
        for query in queries:
            raw_results = requests.get(self.api_link.format(query)).json()

            for product in raw_results["resultados"]:
                extras = {
                    "author": product["autor"],
                    "shipping": "", "sent_from": ""
                }

                name = product["titulo"]
                img = product["capa"]

                if "produto" not in product:
                    # id repetido
                    _id = product["produto_codigo"]
                    if _id in all_ids:
                        continue

                    url = product["url"]
                    price = product["preco_minimo"]
                    extras["condition"] = "novo"
                    details = ""
                    extras["shipping"] = ""

                else:
                    _id = product["produto"]["produto_codigo"]
                    if _id in all_ids:
                        continue

                    url = product["url_livro"]
                    price = product["promocao"]["preco_com_desconto"]
                    extras["condition"] = product["tipo"]
                    details = f'\n{extras["condition"]} - {product["caracteristicas"]}\n'

                    seller = product["vendedor"]
                    extras["sent_from"] = f'\n{seller["cidade"]} - {seller["uf"]}\n'

                    free_shipping = seller.get("frete_gratis", None)
                    if free_shipping:
                        extras["shipping"] = "Frete Grátis!"

                    else:
                        shipping = ""
                        shipping_price = product.get("preco_frete", None)
                        if shipping_price and isinstance(shipping_price, (float, int)):
                            shipping += f"R$ {shipping_price:.2f} "

                        promo_shipping = seller.get("frete_gratis_preco_min", None)
                        if promo_shipping:
                            shipping += f"(Frete Grátis acima de {promo_shipping})"

                        extras["shipping"] = f"\n{shipping}\n" if shipping != "" else ""

                all_ids.add(_id)
                results.append(
                    self.new_product(name, price, url, details, price, img, extras)
                )

        return results

if __name__ == "__main__":
    ready_pages = [ EstanteVirtual(
        link="", index=0, category="books",
        api_link="https://lambda.estantevirtual.com.br/busca/exemplares/{}"
    ) ]
    results = asyncio.run(base.BotBase(ready_pages, True).run())

    print(results)
    # import json
    #with open("estante_virtual.json", "w") as json_file:
    #    json.dump(results, json_file)