from base import Bot

class Terabyte(Bot):
    # Funcionando
    async def get_prices(self, **kwargs):
        page = self.page
        await page.goto(kwargs.get('link'))
        all_results = []

        await page.wait_for_selector('div.col-xs-12.col-sm-12.col-md-12.nopadding')
        # await page.wait_for_selector('row produtos-home mg0')
        #async with page.expect_response(lambda response: response.url == "https://www.terabyteshop.com.br/" and response.status == 200) as response_info:
        #    print("Awaiting")
        #    print(response_info)

        #await response_info.value

        results = await page.evaluate("""
        const produtos = Array.from(document.querySelectorAll('.pbox'));
        const resultados = [];
        produtos.forEach((produto) => {
            if (produto.querySelector('.prod-new-price')){
                const name = produto.innerText.split(',')[0].trim()
                const details = produto.innerText.split('\\\n')[0].trim()
                const price = produto.querySelector('.prod-new-price').innerText.split(' ')[1]
                const oldPrice = produto.querySelector('.prod-old-price').innerText.split(' ')[2]
                const url = produto.querySelector('.commerce_columns_item_image').href
                const img = produto.querySelector('img').src
                resultados.push({name, details, price, oldPrice, url, img})
            }
        })
        resultados
        """)
        for result in results:
            result['price'] = float((result['price'][3:].replace('.', '')).replace(',', '.'))
            all_results.append(result)

        return results

if __name__ == "__main__":
    bot = Terabyte()
    import asyncio
    results = asyncio.run(
        bot.run(headless=True, link="https://www.terabyteshop.com.br")
    )
    print(results)
