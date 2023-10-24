import asyncio
import logging
import re
import traceback
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from playwright.async_api import async_playwright
from playwright.async_api._generated import Browser, BrowserContext, Page


class UserMessages(str, Enum):
    ALL_TAGS_MATCHED = (
        "*{brand}*: SUPER OFERTA PRA VOCE! 😱😱\n"   # Site name
        "\n"
        "🔥🔥🔥 {name}\n"                           # Product name
        "\n"
        "R$ {price:.2f} 💵"                          # Price
        "\n"
    )

    AVG_LOW = (
        "*{brand}*: Baixou de preco!\n"        # Site name
        "\n"
        "🔥🔥 {name}\n"                       # Product name
        "\n"
        "R$ {price:.2f} 💵\n"                  # Price
        "Hist.: {avg}\n"                     # AVG Price
        "\n"
    )

    MATCHED_OFFER = (
        "*{brand}*: Você também pode gostar!\n"    # Site name
        "\n"
        "🔥 {name}\n"                             # Product name
        "\n"
        "R$ {price:.2f} 💵"                        # Price
        "\n"
    )

class BotRunner(ABC):
    link: str
    brand: str
    index: int
    metadata: dict[str, Any]
    messages: Enum = UserMessages

    is_ok: bool
    results: list[dict[str, Any]]

    def __init__(
        self, link: str, index: int, category: str, messages: Enum = UserMessages,
        metadata: dict[str, Any] = {}
    ) -> None:
        self.link = link
        self.index = index
        self.category = category
        self.metadata = metadata
        self.messages = messages

        self.brand = self.__class__.__name__
        self.is_ok = None
        self.results = []

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

    @classmethod
    def promo_message (
        cls, result: dict[str, Any], avarage: float, prct_equal: float
    ):

        format_dict = { "prct_equal": prct_equal, "avg": avarage }
        format_dict.update(result)
        format_dict.update(result["extras"])

        if prct_equal == 1:
            message = cls.messages.ALL_TAGS_MATCHED

        elif format_dict["price"] < avarage:
            message = cls.messages.AVG_LOW

        else:
            message = cls.messages.MATCHED_OFFER

        return message.format(**format_dict)

    def new_product (
        self, name: str, price: str, url: str, details: str = None,
        old_price: str = None, img: str = None, extras: dict[str, Any] = {}
    ):
        product = {
            "bot": self.__class__.__name__, "category": self.category, "name": name,
            "details": details, "price": price, "old_price": old_price, "url": url,
            "img": img, "brand": self.brand, "extras": extras
        }

        if details is None and "," in name:
            product["name"], product["details"] = product["name"].split(",", 1)

        if details is None:
            product["details"] = ""

        splitted = details.split(" ") if details is not None else ""
        if len(splitted) > 15:
            details = " ".join(splitted[:15]) + "..."

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

    async def scroll_to_bottom (
        cls, page: Page, rolls: int = 8, prct: int = 5, wait_before_roll: float = 0.3
    ) -> None:
        for i in range(rolls):
            await page.evaluate(
                f"window.scrollTo(0, document.body.scrollHeight * .{i//2 + prct});"
            ),
            await asyncio.sleep(wait_before_roll)

    @abstractmethod
    async def get_prices (self, tab: Page):
        ...

class BotBase:
    browser: Browser
    context: BrowserContext
    headless: bool

    waiting_pages: list[BotRunner]
    limit_pages: int = 2
    page_time_limit: int = 60 * 5  # Five minutes for tab

    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        "(KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36"
    )

    def __init__(self, waiting_pages: list[BotRunner], headless: bool = True) -> None:
        self.waiting_pages = waiting_pages
        self.headless = headless

    async def run (self) -> list[BotRunner]:
        semaphore = asyncio.Semaphore(self.limit_pages)
        results = []

        async with async_playwright() as playwright:
            self.browser = await playwright.chromium.launch(headless=self.headless)
            self.context = await self.browser.new_context(user_agent=self.user_agent)

            tasks = []
            for tab in self.waiting_pages:
                tasks.append(
                    asyncio.ensure_future(self.run_tab(tab, semaphore))
                )

            for future_task in asyncio.as_completed(tasks):
                bot_result = await future_task
                results.append(bot_result)

            await self.browser.close()

        return results

    async def run_tab (
        self, tab: BotRunner, sem: asyncio.Semaphore
    ) -> BotRunner:
        async with sem:
            page = await self.context.new_page()

            # Get price or None
            bot_full_name = f"{tab.category}|{tab.brand}#{tab.index}"
            logging.warning(f"Trying to run {bot_full_name}")

            try:
                results = await asyncio.wait_for(
                    tab.get_prices(page),
                    60 * 3
                )
                tab.is_ok = True
                tab.results = results
                logging.warning(
                    f"{bot_full_name}: {len(results)} found products."
                )
            except TimeoutError as exc:
                tab.is_ok = False
                f"{bot_full_name}: Timeout"
            except Exception as exc:
                tab.is_ok = False
                logging.error(
                    f"{bot_full_name}: Error ({str(exc)})."
                )

            await page.close()

            return tab
