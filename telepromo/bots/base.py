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
        "links": [
            {
                "name": "Madeira Madeira",
                "link": ""
            }]
    },
    {
        "name": "livros",
        "links": [
        {
            "name": "Estante Virtual",
            "link": ""
        }]
    }
]

from playwright.async_api import async_playwright
from playwright.async_api._generated import BrowserType, Page
from abc import abstractmethod, ABC

class Bot(ABC):
    browser: BrowserType
    page: Page
    headless: bool
    user_agent: str = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36"
    )

    async def run(self, **kwargs):
        headless = kwargs.get("headless", True)

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

    @abstractmethod
    async def get_prices(self):
        ...