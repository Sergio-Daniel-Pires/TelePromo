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
                "link": "https://www.kabum.com.br/ofertas/megamaio",
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
from abc import abstractmethod, ABC

class Bot(ABC):
    browser: object

    async def run(self, **kwargs):
        #self.browser = playwright.chromium.launch(headless=True)
        #self.context = self.browser.new_context()
        async with async_playwright() as playwright:
            self.browser = playwright.chromium.launch(headless=True)

            result = await self.get_prices(**kwargs)

            self.browser.close()
        
        return result

    @abstractmethod
    async def get_prices(self):
        ...