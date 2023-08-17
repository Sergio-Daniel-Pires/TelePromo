from base import Bot

class EstanteVirtual(Bot):
    async def get_prices(self, **kwargs):
        page = self.page
        await page.goto(kwargs.get("link"))
        all_results = []

        # Erro de waiting to be visible
        await page.wait_for_selector("div.VueCarousel-wrapper")

        results = await page.evaluate("""
        const produtos = Array.from(document.querySelectorAll(".pbox"));
        const resultados = [];
        produtos.forEach((produto) => {
            const name = produto.innerText.split(",")[0].trim()
            const details = produto.innerText.split("\\\n")[0].trim()
            const price = produto.querySelector(".prod-new-price").innerText.split(" ")[1]
            const oldPrice = produto.querySelector(".prod-old-price").innerText.split(" ")[2]
            const url = produto.querySelector(".commerce_columns_item_image").href
            const img = produto.querySelector("img").src
            resultados.push({name, details, price, oldPrice, url, img})
        })
        resultados
        """)
        for result in results:
            result["price"] = float((result["price"][3:].replace(".", "")).replace(",", "."))
            all_results.append(result)
            """
            next_button_class = document.querySelector("a[class="nextLink"]")
            next_button = await page.evaluate(next_button_class)
            if next_button is None:
                break

            next_button = await page.evaluate(next_button_class + ".click()")
            """

        return results


if __name__ == "__main__":
    bot = EstanteVirtual()
    import asyncio
    results = asyncio.run(
        bot.run(headless=True, link="https://www.terabyteshop.com.br/")
    )
