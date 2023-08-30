import asyncio
import logging

from project.database import Database
from project.metrics_collector import MetricsCollector
from project.monitor import Monitoring
from project.telegram_bot import TelegramBot
from project.utils import DAYS_IN_YEAR, MINUTES_IN_DAY
from project.vectorizers import Vectorizers

async def verify_urls_price (monitor: Monitoring, link_obj: dict):
    url_list = link_obj["links"]
    category = link_obj["category"]

    # Get raw results from web scraping
    results = await monitor.prices_from_url(url_list, category)

    # Get real metrics from last scan
    await monitor.verify_save_prices(results, category)

    return True

async def continuous_verify_price (db: Database, monitor: Monitoring):

    for _ in range(DAYS_IN_YEAR):

        for _ in range(MINUTES_IN_DAY):
            links_cursor = db.get_links()

            logging.info("Starting requests...")
            for link_obj in links_cursor:
                await verify_urls_price(monitor, link_obj)

            await asyncio.sleep(10)


async def main ():
    metrics = MetricsCollector(9091)

    db = Database(metrics)
    vectorizers = Vectorizers()
    telegram_bot = TelegramBot(
        database=db,
        vectorizer=vectorizers,
        metrics_collector=metrics
    )
    monitor = Monitoring(
        retry=3,
        database=db,
        telegram_bot=telegram_bot,
        vectorizer=vectorizers,
        metrics_collector=metrics
    )

    await telegram_bot.iniatilize()
    await continuous_verify_price(db, monitor)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
