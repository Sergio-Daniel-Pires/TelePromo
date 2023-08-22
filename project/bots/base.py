import logging
import re
import traceback
from abc import ABC, abstractmethod

from playwright.async_api import async_playwright
from playwright.async_api._generated import BrowserType, Page

LINKS = [
    {
        "name": "diversificado",
        "links": [
            {
                "name": "MagaLu",
                "link": ""
            }]
    },
    {
        "name": "eletronicos",
        "links": [
            {
                "name": "Kabum",
                "link": "https://www.kabum.com.br",
                "repeat": "60",
                "last":  "2023-05-11 00:30:03.354898"
            },
            {
                "name": "Terabyte",
                "link": ""
            },
            {
                "name": "Pichau",
                "link": ""
            }]
    },
    {
        "name": "roupas",
        "links": [
            {
                "name": "Centauro",
                "link": ""
            },
            {
                "name": "Nike",
                "link": ""
            },
            {
                "name": "Adidas",
                "link": ""
            },
            {
                "name": "Dafiti",
                "link": ""
            }]
    },
    {
        "name": "casa/domestico",
        "links": [{
            "name": "Madeira Madeira",
            "link": ""
        }]
    },
    {
        "name": "livros",
        "links": [{
            "name": "Estante Virtual",
            "link": ""
        }]
    }
]


class Bot (ABC):
    browser: BrowserType
    link: str
    page: Page
    headless: bool
    brand: str
    user_agent: str = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/61.0.2935 Safari/537.36"
    )

    async def run (self, **kwargs):
        headless = kwargs.get("headless", True)
        self.link = kwargs["link"]
        self.brand = kwargs.get("brand", "Teste")

        async with async_playwright() as playwright:
            self.browser = await playwright.chromium.launch(
                headless=headless
            )
            self.page = await self.browser.new_page(
                user_agent=self.user_agent
            )

            result = await self.get_prices(**kwargs)

            await self.browser.close()

        return result

    @classmethod
    def format_money (cls, value: str) -> float:
        if type(value) in (int, float):
            return value

        clean_string = value
        try:
            clean_string = re.sub(r"[^\d.,]", "", clean_string)
            clean_string = re.sub(r",", ".", clean_string)
            clean_string = re.sub(r"\.(\d{3})", r"\1", clean_string)

            return float(clean_string)

        except Exception:
            logging.error(f"'{clean_string}' ({type(clean_string)}) is not a valid float!")
            logging.error(traceback.format_exc())
            return None

    def new_product (
        self, name: str, price: str, url: str, details: str = None,
        old_price: str = None, img: str = None
    ):
        product = {
            "name": name, "details": details, "price": price,
            "old_price": old_price, "url": url, "img": img, "brand": self.brand
        }

        for key in ( "price", "old_price" ):
            product[key] = self.format_money(product[key])

        for key in ( "img", "url" ):
            value = product[key]
            if value and not value.startswith("https://"):
                product[key] = self.link + product[key]

        return product

    @abstractmethod
    async def get_prices (self):
        ...
