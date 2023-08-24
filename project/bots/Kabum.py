import logging
import re
import traceback

import requests

try:
    from project.bots.base import Bot
except Exception:
    from base import Bot


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

        api_link = (
            "https://b2lq2jmc06.execute-api.us-east-1.amazonaws.com/PROD/ofertas?&"
            "campanha=SEMANAGAMER&pagina=1&limite=1000&"
            "marcas=&ordem=&valor_min=&valor_max=&estrelas=&desconto_minimo="
            "&desconto_maximo=&dep=&sec=&vendedor_codigo=&string=&app=1"
        )

        try:
            response = requests.get(api_link)
            response = response.json()

            for offer in response["produtos"] + response["encerradas"]:
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

                logging.debug(__class__, old_price, price)
                results.append(
                    self.new_product(name, price, url, details, old_price, img)
                )

            return results

        except Exception as exc:
            logging.error(traceback.format_exc())
            logging.error(f"Invalid response: {exc}")

        await page.goto(self.link)

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


if __name__ == "__main__":
    bot = Kabum()
    import asyncio
    results = asyncio.run(
        bot.run(headless=True, link="https://www.kabum.com.br/ofertas/SEMANAGAMER")
    )
    print(results)
