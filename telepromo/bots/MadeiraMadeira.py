from base import Bot

class MadeiraMadeira(Bot):
    """
    Erros:
    img nao funciona
    """
    async def get_prices(self, **kwargs):
        page = self.page
        await page.goto(kwargs.get('link'))
        all_results = []

        await page.wait_for_selector('.cav--c-eNhzRw.cav--c-eNhzRw-fyOwyl-sm-6.cav--c-eNhzRw-fLxfDQ-md-4.cav--c-eNhzRw-AfAoe-lg-3')
        await asyncio.sleep(1)

        results = await page.evaluate("""
        const produtos = Array.from(document.querySelectorAll('article > a'));
        const resultados = [];
        produtos.forEach((produto) => {
            current_result = {}
            const name = produto.querySelector('h2').innerText;
            const details = name;
            const price = produto.querySelector('span.cav--c-gNPphv-hyvuql-weight-bold').innerText;
            const oldPrice = produto.querySelector('span.cav--c-gNPphv.cav--c-gNPphv-iihFNG-size-bodyXSmall.cav--c-gNPphv-ijymXNu-css');
            const url = produto.href;
            const img = produto.querySelector('img.main-img').src;
            current_result = {name, details, price, url, img}
            if (oldPrice){
                current_result['oldPrice'] = oldPrice.innerText.slice(3)
            }
            resultados.push(current_result);
        })
        resultados
        """)

        all_results += results
        for result in results:
            result['price'] = float((result['price'].replace('.', '')).replace(',', '.'))
            if 'oldPrice' in result:
                result['oldPrice'] = float((result['oldPrice'].replace('.', '')).replace(',', '.'))

            if not result['img'].startswith('https://'):
                result['img'] = None

            all_results.append(result)

        return results


if __name__ == "__main__":
    bot = MadeiraMadeira()
    import asyncio
    results = asyncio.run(
        bot.run(headless=True, link="https://www.madeiramadeira.com.br/ofertas-do-dia")
    )
    print(results)
