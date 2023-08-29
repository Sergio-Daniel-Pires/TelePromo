import logging
import re
import traceback
from abc import ABC, abstractmethod

from playwright.async_api import async_playwright
from playwright.async_api._generated import BrowserType, Page

import asyncio


class Bot (ABC):
    browser: BrowserType
    link: str
    page: Page
    headless: bool
    brand: str
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        "(KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36"
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

    async def scroll_to_bottom (
        self, rolls: int = 8, prct: int = 5, wait_before_roll: float = 0.3
    ) -> None:
        for i in range(rolls):
            await self.page.evaluate(
                f"window.scrollTo(0, document.body.scrollHeight * .{i//2 + prct});"
            ),
            await asyncio.sleep(wait_before_roll)

    def new_product (
        self, name: str, price: str, url: str, details: str = None,
        old_price: str = None, img: str = None, shipping: str = None,
        from_brazil: bool = True, **kwargs
    ):
        product = {
            "bot": self.__class__.__name__, "name": name, "details": details,
            "price": price, "old_price": old_price, "url": url, "img": img,
            "brand": self.brand, "shipping": shipping
        }

        if details is None and "," in name:
            product["name"], product["details"] = product["name"].split(",", 1)

        if details is None:
            product["details"] = ""

        for key in ( "name", "details" ):
            if product[key]:
                product[key] = product[key].strip()

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
