import asyncio
import logging
import time
from prometheus_client import start_http_server

from project.database import Database
from project.metrics_collector import MetricsCollector
from project.graphs import GroupMetrics
from project.monitor import Monitoring
from project.telegram_bot import TelegramBot
from project.utils import DAYS_IN_YEAR, MINUTES_IN_DAY, SECONDS_IN_DAY, SECONDS_IN_HOUR
from project.vectorizers import Vectorizers

async def verify_urls_price (monitor: Monitoring, link_obj: dict):
    url_list = link_obj["links"]
    category = link_obj["name"]

    # Get raw results from web scraping
    results = await monitor.prices_from_url(url_list)

    # Get real metrics from last scan
    new_metric = await monitor.verify_save_prices(results, category)

    return new_metric

async def continuous_verify_price (db: Database, monitor: Monitoring):
    semaphore = asyncio.Semaphore(1)

    _ = GroupMetrics()
    for _ in range(DAYS_IN_YEAR):
        diary_stamp = int(time.time())
        hourly_results = GroupMetrics()

        for _ in range(MINUTES_IN_DAY):
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

            while int(time.time()) - start_date < SECONDS_IN_HOUR:
                await asyncio.sleep(10)


async def main ():
    metrics = MetricsCollector(9091)

    db = Database(metrics)
    vectorizers = Vectorizers()
    telegram_bot = TelegramBot(
        database=db,
        vectorizer=vectorizers,
        metrics=metrics
    )
    monitor = Monitoring(
        retry=3,
        database=db,
        telegram_bot=None,
        vectorizer=vectorizers,
        metrics_collector=metrics
    )

    await telegram_bot.iniatilize()
    await continuous_verify_price(db, monitor)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
