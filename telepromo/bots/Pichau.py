from base import Bot

class Pichau(Bot):
    async def get_prices(self, **kwargs):
        page = self.page
        await page.goto(kwargs.get('link'), timeout=0)
        all_results = []

        await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")

        await asyncio.sleep(1)

        await page.wait_for_selector("section.jss114")

        results = await page.evaluate("""
        const produtos = Array.from(document.querySelectorAll('a[data-cy="list-product"]'));
        const resultados = [];
        produtos.forEach((produto) => {
            const name = produto.querySelector('h2').innerText;
            const details = name;
            const price = produto.querySelector('.jss151').innerText;
            const oldPrice = produto.querySelector('div.jss163 s');
            const url = produto.href;
            const img = produto.querySelector('img.jss133').src;
            resultados.push({name, details, price, oldPrice, url, img});
        })
        resultados
        """)

        all_results += results

        return results

if __name__ == "__main__":
    bot = Pichau()
    import asyncio
    results = asyncio.run(
        bot.run(headless=False, link="https://www.pichau.com.br")
    )
    print(results)
