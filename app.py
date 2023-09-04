from telegram.ext import ContextTypes
import logging
import os
import signal

from project.database import Database
from project.metrics_collector import MetricsCollector
from project.monitor import Monitoring
from project.telegram_bot import TelegramBot
from project.vectorizers import Vectorizers

def update_all_mongo (database: Database, vectorizer: Vectorizers):
    all_products_without_adjectives = database.find_all_without_adjectives()

    for product in all_products_without_adjectives:
        old_tags = product["tags"]
        raw_name = product["raw_name"]
        category = product["category"]

        if category == "eletronicos":
            new_tags, adjectives = vectorizer.extract_tags(raw_name, "")
        else:
            new_tags, adjectives = old_tags, []
        
        database.set_adjetives(old_tags, new_tags, adjectives)

def main ():
    metrics = MetricsCollector(9091)

    db = Database(metrics)
    vectorizers = Vectorizers()
    update_all_mongo(db, vectorizers)

    telegram_bot = TelegramBot(
        database=db,
        vectorizer=vectorizers,
        metrics_collector=metrics
    )

    monitor = Monitoring(
        retry=3,
        database=db,
        vectorizer=vectorizers,
        metrics_collector=metrics
    )

    async def continuous_verify_price (context: ContextTypes.DEFAULT_TYPE):
        links_cursor = db.get_links()

        logging.info("Starting requests...")
        for link_obj in links_cursor:
            url_list = link_obj["links"]
            category = link_obj["category"]

            # Get raw results from web scraping
            results = await monitor.prices_from_url(url_list, category)

            await monitor.verify_save_prices(context, results, category)

    telegram_bot.application.job_queue.run_repeating(
        continuous_verify_price, 10, first=0
    )

    try:
        telegram_bot.application.run_polling()
    except:
        os.kill(os.getpid(), signal.SIGTERM)

if __name__ == "__main__":
    main()
