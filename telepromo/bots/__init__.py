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
                "link": "https://www.kabum.com.br/ofertas/megamaio?pagina=53"
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

from playwright.sync_api import sync_playwright
from abc import abstractmethod, ABC

class Bot(ABC):
    browser: object

    def run(self, **kwargs):
        #self.browser = playwright.chromium.launch(headless=True)
        #self.context = self.browser.new_context()
        with sync_playwright() as playwright:
            self.browser = playwright.chromium.launch(headless=True)

            result = self.get_prices(**kwargs)

            self.browser.close()
        
        return result

    @abstractmethod
    def get_prices(self):
        ...