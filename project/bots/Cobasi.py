import logging
import re
import traceback

import requests
import asyncio

try:
    from project.bots.base import Bot
except Exception:
    from base import Bot

class Cobasi (Bot):
    async def get_prices (self, **kwargs):
        page = self.page

        max_pages = 100
        last = None

        results = []

        api_link = (
            "https://mid-back.cobasi.com.br/search/products?hotsite=menu-de-promocoes"
            "&sortby=relevance&resultsperpage=2000&name=menu-de-promocoes&page={}&apikey=cobasi"
        )

        try:
            for page in range(max_pages):
                response = requests.get(api_link.format(page))
                response = response.json()

                if last is None:
                    raw_last = response.get("pagination", {}).get("last", "page=20")
                    pattern = r"&page=(\d+)"

                    re_result = re.findall(pattern, raw_last)
                    if len(re_result) == 0:
                        last = 20
                    else:
                        last = int(re_result[0])

                if page >= last:
                    break

                for offer in response["products"]:
                    if offer["status"] != "AVAILABLE":
                        continue

                    name = offer["name"]
                    details = ", ".join(sku["specs"]["default"][0] for sku in offer["skus"])

                    price = offer["price"]
                    old_price = offer["oldPrice"]
                    sub_price = offer["subscriptionPrice"]

                    if None in (price, old_price):
                        continue

                    img = offer["images"]["default"]
                    url = offer["url"]

                    logging.debug(__class__, old_price, price)
                    results.append(
                        self.new_product(
                            name, price, url, details, old_price, img, sub_price=sub_price
                        )
                    )

            return results

        except Exception as exc:
            logging.error(traceback.format_exc())
            logging.error(f"Invalid response: {exc}")

        return results


if __name__ == "__main__":
    bot = Cobasi()
    results = asyncio.run(
        bot.run(headless=True, link="https://www.cobasi.com.br/promocoes")
    )
    print(len(results))
