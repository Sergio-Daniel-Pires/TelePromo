from database import Database
from monitor import Monitoring
from vectorizers import Vectorizers
from telegram_bot import TelegramBot
from graphs import GroupMetrics

import asyncio
import logging
import time

from utils import DAYS_IN_YEAR, MINUTES_IN_DAY, SECONDS_IN_DAY, SECONDS_IN_HOUR

def send_summary ():
    ...

async def verify_urls_price (monitor: Monitoring, link_obj: dict):
    url_list = link_obj["links"]
    category = link_obj["name"]
    results = await monitor.prices_from_url(url_list)  # Get raw results from web scraping
    new_metric = await monitor.verify_save_prices(results, category)  # Get real metrics from last scan

    return new_metric

async def continuous_verify_price (db: Database, monitor: Monitoring):
    semaphore = asyncio.Semaphore(1)

    daily_metrics = GroupMetrics()
    for _ in range(DAYS_IN_YEAR):
        diary_stamp = int(time.time())

        hourly_results = GroupMetrics()
        for minute in range(MINUTES_IN_DAY):
            start_date = int(time.time())
            tasks = []
            links_cursor = db.get_links()

            for link_obj in links_cursor:
                async with semaphore:
                    tasks.append(asyncio.ensure_future(verify_urls_price(monitor, link_obj)))

            logging.info("Starting requests...")
            for future_task in asyncio.as_completed(tasks):
                new_metric = await future_task
                print(new_metric)
                hourly_results.add_or_update_one(new_metric)

            # Verifica se o dia acabou e tem que enviar relatorio
            finish_date = int(time.time())
            if (finish_date - diary_stamp) >= SECONDS_IN_DAY:
                break

            # Espera uma hora antes das proximas chamadas
            elapsed = finish_date - start_date
            remaining = SECONDS_IN_HOUR - elapsed
            logging.warning(f"Runned too fast, waiting {remaining} seconds.")

            if elapsed < SECONDS_IN_HOUR:
                await asyncio.sleep(remaining)


async def main ():
    db = Database()
    vectorizers = Vectorizers()
    telegram_bot = TelegramBot(
        database=db,
        vectorizer=vectorizers
    )
    monitor = Monitoring(
        retry=3,
        database=db,
        telegram_bot=telegram_bot,
        vectorizer=vectorizers
    )

    await telegram_bot.iniatilize()
    await continuous_verify_price(db, monitor)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
