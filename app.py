from project.database import Database
from project.metrics_collector import MetricsCollector
from project.monitor import Monitoring
from project.telegram_bot import TelegramBot
from project.vectorizers import Vectorizers
from redis import Redis
import threading
import asyncio

import logging

logging.getLogger().setLevel(logging.WARNING)

def main ():
    metrics = MetricsCollector(9091)

    db = Database(metrics)
    vectorizers = Vectorizers()

    redis_client = Redis(host="redis", port=6379)

    telegram_bot = TelegramBot(
        database=db,
        vectorizer=vectorizers,
        metrics_collector=metrics,
        redis_client=redis_client
    )

    monitor = Monitoring(
        retry=3,
        database=db,
        vectorizer=vectorizers,
        redis_client=redis_client,
        metrics_collector=metrics
    )

    telegram_bot.application.job_queue.run_once(
       telegram_bot.send_ngrok_message, 2
    )

    telegram_bot.application.job_queue.run_repeating(
        telegram_bot.get_user_msgs_from_redis, 60, 5
    )

    # Start Verify prices in a new Thread
    threading.Thread(
        target=asyncio.run, args=(monitor._continuous_verify_price(),)
    ).start()

    telegram_bot.application.run_polling()

if __name__ == "__main__":
    main()
