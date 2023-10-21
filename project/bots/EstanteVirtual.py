from playwright.async_api import Page

try:
    from project.bots.base import BotRunner
except Exception:
    from base import BotRunner


class EstanteVirtual (BotRunner):
    async def get_prices (self, page: Page):
        results = []

        await page.route("**/*", lambda route: route.abort()
            if route.request.resource_type == "image"
            else route.continue_()
        )

        await page.goto(self.link)

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
            results.append(result)
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
