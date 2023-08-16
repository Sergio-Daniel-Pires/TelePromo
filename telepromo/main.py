from database import Database
from monitor import Monitoring
from vectorizers import Vectorizers
from telegram_bot import TelegramBot

import asyncio
from datetime import datetime
import logging

DAYS_IN_YEAR = 365
MINUTES_IN_DAY = 1440

async def verify_urls_price(monitor: Monitoring, current_obj: dict):
    url_list = current_obj['links']
    results = await monitor.prices_from_url(url_list)
    new_prices = await monitor.verify_save_prices(results)
    return new_prices

async def continuos_verify_price(db: Database, monitor: Monitoring):
    semaphore = asyncio.Semaphore(4)
    for day in range(DAYS_IN_YEAR):
        day_date = datetime.today()
        day_results = {
            "Ofertas alertadas": 0,
            "Enviadas no grupo": 0,
            "Produtos novos": 0
        }

        for minute in range(MINUTES_IN_DAY):
            minute_date = datetime.today()
            tasks = []
            links_cursor = db.get_links()
            for current_obj in links_cursor:
                async with semaphore:
                    tasks.append(asyncio.ensure_future(verify_urls_price(monitor, current_obj)))
            
            results = await asyncio.gather(*tasks)

            # Verifica se o dia acabou e tem que enviar relatorio
            date_now = datetime.today()
            if (date_now - day_date).days > 0:
                break
            # Caso as consultas sejam mais rapido que um minuto, espera 1 minuto
            if (date_now - minute_date).seconds < 60:
                remaining = 60 - (date_now - minute_date).seconds
                logging.warning(f"Runned too fast, waiting {remaining} seconds.")
                await asyncio.sleep(remaining)

async def main():
    db = Database()
    vectorizers = Vectorizers()
    telegram_bot = TelegramBot(
        database = db,
        vectorizer = vectorizers
    )
    monitor = Monitoring(
        retry = 3,
        database = db,
        telegram_bot = telegram_bot,
        vectorizer = vectorizers
    )

    await telegram_bot.iniatilize()
    await continuos_verify_price(db, monitor)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()