from base import Bot

import time

class Pichau(Bot):
    """
    Erros:
    Carrosel carrega nunk   
    """

    async def scroll_to_bottom(self, page) -> None:
        for i in range(8):
            await asyncio.wait([
                page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * .{i//2 + 5});"),
                asyncio.sleep(0.3)
            ])

    async def get_prices(self, **kwargs):
        page = self.page
        
        page.on("console", lambda msg: print(f"error: {msg.text}") if msg.type == "error" else None)
        
        await page.goto(kwargs.get('link'), timeout=0, wait_until="domcontentloaded")
        all_results = []

        await page.evaluate("window.scrollTo(0, document.body.scrollHeight * .2);")
        
        try:
            await page.wait_for_selector("a[data-cy='list-product']")
        except Exception as exc:
            await page.screenshot(path="Pichau.jpg")
            
            raise exc
        
        await self.scroll_to_bottom(page)

        async with page.expect_console_message() as msg_info:
            results = await page.evaluate(
            """
            const resultados = [];
            try {
                const section_2 = document.querySelectorAll("section")[1];
                const produtos = Array.from(section_2.querySelectorAll('a[data-cy="list-product"]'));
                try {
                    produtos.forEach((produto) => {
                        const name = produto.querySelector('h2').innerText;
                        const details = name;
                        const price = produto.querySelector('.MuiCardContent-root > div :nth-child(3)').innerText;
                        const oldPrice = produto.querySelector('.MuiCardContent-root > div :nth-child(1) > div > div > s').innerText;
                        const url = produto.href;
                        const img = produto.querySelector('img').src;
                        resultados.push({name, details, price, oldPrice, url, img});
                    })
                } catch (e) {console.log("Erro for: ", e)}
                console.log("Sucess")
            } catch (e) {
                console.log("Erro: ", e);
            }
            resultados
            """
            )
            print(await msg_info.value)

            all_results += results

        return results

if __name__ == "__main__":
    bot = Pichau()
    import asyncio
    results = asyncio.run(
        bot.run(headless=False, link="https://www.pichau.com.br")
    )
    print(results)
