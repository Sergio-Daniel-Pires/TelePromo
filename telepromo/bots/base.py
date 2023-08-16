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

    async def run(self, **kwargs):
        async with async_playwright() as playwright:
            self.browser = await playwright.chromium.launch(headless=kwargs.get('headless', True))
            self.page = await self.browser.new_page()

            result = await self.get_prices(**kwargs)

            await self.browser.close()
        
        return result

    @abstractmethod
    async def get_prices(self):
        ...