import logging
import re
import traceback
from enum import Enum
from typing import Any

import requests

try:
    from project.bots.base import Bot
except Exception:
    from base import Bot


class KabumMessages(str, Enum):
    ALL_TAGS_MATCHED = (
        "*{}*: OFERTA NINJA PRA VOCÊ! 🥷😱\n"   # Site name
        "\n"
        "🔥🔥🔥 {}\n"                           # Product name
        "\n"
        "Preço 💵\n"
        "R$ {:.2f}"                          # Price
        "\n"
        "\n"
        "🥷 Prime\n"
        "R$ {:.2f}"                          # Prime price
        "\n"
    )

    AVG_LOW = (
        "*{}*: Baixou de preco!\n"        # Site name
        "\n"
        "🔥🔥 {}\n"                       # Product name
        "Preço 💵\n"
        "\n"
        "R$ {:.2f}\n"                  # Price
        "Hist.: {}\n"                     # AVG Price
        "\n"
        "\n"
        "🥷 Prime\n"
        "R$ {:.2f}"                    # Prime price
        "\n"
    )

    MATCHED_OFFER = (
        "*{}*: 🥷 Ninja recomenda!\n"    # Site name
        "\n"
        "🔥 {}\n"                        # Product name
        "\n"
        "Preço 💵\n"
        "R$ {:.2f}"                   # Price
        "\n"
        "🥷 Prime\n"
        "R$ {:.2f}"                   # Prime price
        "\n"
    )

def name_to_url(text: str) -> str:
    # Substituir espaços por hífens
    transformed_string = text.replace(" ", "-")

    # Remover caracteres especiais usando expressão regular
    transformed_string = re.sub(r'[^\w\s-]', '', transformed_string)

    # Substituir múltiplos hífens por um único hífen
    transformed_string = re.sub(r'[-\s]+', '-', transformed_string)

    # Converter para minúsculas
    transformed_string = transformed_string.lower()

    return transformed_string

class Kabum (Bot):
    async def get_prices (self, **kwargs):
        page = self.page
        results = []

        await page.goto(self.link)

        await page.wait_for_selector("#bannerPrincipal")

        for campanha_bruta in await page.query_selector_all("#bannerPrincipal"):
            campanha_href = await campanha_bruta.get_attribute("href")

            if campanha_href.startswith("/ofertas/"):
                campanha = campanha_href.split("/")[-1]

        try:
            api_link = (
                f"https://b2lq2jmc06.execute-api.us-east-1.amazonaws.com/PROD/ofertas?&campanha={campanha}"
                "&pagina=1&limite=1000&marcas=&ordem=&valor_min=&valor_max=&estrelas=&desconto_minimo="
                "&desconto_maximo=&dep=&sec=&vendedor_codigo=&string=&app=1"
            )
            print(api_link)

            response = requests.get(api_link).json()

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

                logging.debug(__class__, old_price, price)
                results.append(
                    self.new_product(name, price, url, details, old_price, img, extras)
                )

            return results

        except Exception as exc:
            logging.error(traceback.format_exc())
            logging.error(f"Invalid response: {exc}")

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

    def promo_message (
        self, result: dict[str, Any], avarage: float, prct_equal: float
    ):
        brand = result["brand"]
        product_name = result["name"]
        details = result["details"].strip()
        price = result["price"]
        url = result["url"]
        img = result["img"]

        prime_price = result["extras"].get("prime_price", price)

        if product_name == details:
            details = ""

        product_desc = f"{product_name}, {details}"

        if prct_equal == 1:
            message = KabumMessages.ALL_TAGS_MATCHED.format(
                brand, product_desc, price, prime_price, img, url
            )

        elif price < avarage:
            message = KabumMessages.AVG_LOW.format(
                brand, product_desc, price, avarage, prime_price, img, url
            )

        else:
            message = KabumMessages.MATCHED_OFFER.format(
                brand, product_desc, price, prime_price, img, url
            )

        return message


if __name__ == "__main__":
    bot = Kabum()
    import asyncio
    results = asyncio.run(
        bot.run(headless=False, link="https://www.kabum.com.br/")
    )
    print(results)
