from base import Bot

class Kabum(Bot):
    async def get_prices(self, **kwargs):
        page = self.page
        await page.goto(kwargs.get('link'))
        all_results = []

        await page.wait_for_selector("section#blocoProdutosListagem")

        results = await page.evaluate("""
        const produtos = Array.from(document.querySelectorAll('.nameCard'));
        const resultados = [];
        produtos.forEach((produto) => {
            const name = produto.innerText.split(',')[0].trim();
            const details = produto.innerText.substr(produto.innerText.indexOf(',') + 1).trim();
            const price = produto.parentElement.parentElement.parentElement.parentElement.querySelector('.priceCard').innerText;
            const url = produto.parentElement.parentElement.parentElement.parentElement.parentElement.href;
            const img = produto.parentElement.parentElement.parentElement.parentElement.parentElement;
            resultados.push({name, details, price, url});
        })
        resultados;
        """)
        for result in results:
            result['price'] = float((result['price'][3:].replace('.', '')).replace(',', '.'))
            all_results.append(result)

        return results

if __name__ == "__main__":
    bot = Kabum()
    import asyncio
    results = asyncio.run(
        bot.run(headless=True, link="https://www.kabum.com.br/ofertas/BLACKNINJA")
    )
    print(results)
