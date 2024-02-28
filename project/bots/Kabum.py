import asyncio
import logging
import re
import traceback
from enum import Enum
from typing import Any

import requests
from playwright.async_api import Page

try:
    from project.bots import base
except Exception:
    import base


class KabumMessages(str, Enum):
    ALL_TAGS_MATCHED = (
        "*{brand}*: OFERTA NINJA PRA VOCÊ! 🥷😱\n"
        "\n"
        "🔥🔥🔥 {name}\n"
        "\n"
        "Preço 💵\n"
        "R$ {price:.2f}"
        "\n"
        "\n"
        "🥷 Prime\n"
        "R$ {prime_price:.2f}"
        "\n"
    )

    AVG_LOW = (
        "*{brand}*: Baixou de preco!\n"
        "\n"
        "🔥🔥 {name}\n"
        "Preço 💵\n"
        "\n"
        "R$ {price:.2f}\n"                  # Price
        "Hist.: {avg}\n"                     # AVG Price
        "\n"
        "\n"
        "🥷 Prime\n"
        "R$ {prime:.2f}"                    # Prime price
        "\n"
    )

    MATCHED_OFFER = (
        "*{brand}*: 🥷 Ninja recomenda!\n"    # Site name
        "\n"
        "🔥 {name}\n"                        # Product name
        "\n"
        "Preço 💵\n"
        "R$ {price:.2f}"                   # Price
        "\n"
        "🥷 Prime\n"
        "R$ {prime_price:.2f}"                   # Prime price
        "\n"
    )

def name_to_url (text: str) -> str:
    # Substituir espaços por hífens
    transformed_string = text.replace(" ", "-")

    # Remover caracteres especiais usando expressão regular
    transformed_string = re.sub(r'[^\w\s-]', '', transformed_string)

    # Substituir múltiplos hífens por um único hífen
    transformed_string = re.sub(r'[-\s]+', '-', transformed_string)

    # Converter para minúsculas
    transformed_string = transformed_string.lower()

    return transformed_string

class Kabum (base.BotRunner):
    messages: Enum = KabumMessages

    def __init__(
        self, link: str, index: int, category: str, messages: Enum = ...,
        metadata: dict[str, Any] = {}, api_link: str = None
    ) -> None:
        super().__init__(link, index, category, messages, metadata, api_link)
        self.messages = KabumMessages

    async def get_prices (self, page: Page):
        results = []

        await page.route("**/*", lambda route: route.abort()
            if route.request.resource_type == "image"
            else route.continue_()
        )

        await page.goto(self.link, timeout=30000)

        await page.wait_for_selector("#bannerPrincipal")

        await page.wait_for_selector("section#blocoProdutosListagem")

        products = await page.query_selector_all("div.productCard")

        for product_obj in products:
            name_and_details = await (await product_obj.query_selector(".nameCard")).inner_text()
            name, details = name_and_details.split(",", 1)

            price = await (await product_obj.query_selector(".priceCard")).inner_text()
            old_price = await (await product_obj.query_selector(".oldPriceCard")).inner_text()

            url = await (await product_obj.query_selector(".productLink")).get_attribute("href")
            img = await (await product_obj.query_selector(".imageCard")).get_attribute("src")

            results.append(
                self.new_product(name, price, url, details, old_price, img)
            )

        return results

    async def get_prices_from_api(self):
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            "(KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36"
        )

        api_link = (
            "https://b2lq2jmc06.execute-api.us-east-1.amazonaws.com/PROD/ofertas?"
            "&campanha={}&pagina=1&limite=1000&marcas=&ordem=&valor_min=&valor_max="
            "&estrelas=&desconto_minimo=&desconto_maximo=&dep=&sec=&vendedor_codigo=&string=&app=1"
        )

        page = requests.get(self.link, headers={"User-Agent": user_agent}).text
        campanhas = set(re.findall(r'href=\"\/ofertas\/(\w+.)\"', page))

        results = []

        for campanha in campanhas:
            try:
                response = requests.get(api_link.format(campanha)).json()

                for offer in response["produtos"]:  # + response["encerradas"]:
                    extras = {}

                    name_and_details = offer["produto"]
                    if "," in name_and_details:
                        name, details = name_and_details.split(",", 1)
                    else:
                        name = details = name_and_details

                    price = offer["vlr_oferta"]
                    old_price = offer["vlr_normal"]

                    if price is None:
                        price = old_price

                    if None in (price, old_price):
                        continue

                    img = offer["imagem"]

                    url_name = name_to_url(name_and_details)
                    url = f"https://www.kabum.com.br/produto/{offer['codigo']}/{url_name}"

                    # extras
                    prime_price = self.format_money(offer.get("preco_desconto_prime", price))
                    extras["prime_price"] = (
                        prime_price if prime_price != 0 else self.format_money(price)
                    )

                    results.append(
                        self.new_product(name, price, url, details, old_price, img, extras)
                    )

            except Exception as exc:
                logging.error(traceback.format_exc())
                logging.error(f"Invalid response: {exc}")

        return results

if __name__ == "__main__":
    ready_pages = [ Kabum(
        link="https://www.kabum.com.br/", index=0, category="eletronics",
        api_link=""
    ) ]
    results = asyncio.run(base.BotBase(ready_pages, True).run())

    print(results)
