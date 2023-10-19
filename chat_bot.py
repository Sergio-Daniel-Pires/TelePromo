import logging
import os

from redis import Redis

from project.database import Database
from project.metrics_collector import MetricsCollector
from project.telegram_bot import TelegramBot, ImportantJobs
from project.vectorizers import Vectorizers

logging.getLogger().setLevel(logging.WARNING)

def main ():
    metrics = MetricsCollector(9092)

    db = Database(metrics)
    vectorizers = Vectorizers()

    redis_client = Redis(
        host=os.environ.get('REDIS_URL', 'localhost'), port=6379
    )

    telegram_bot = TelegramBot(
        database=db,
        vectorizer=vectorizers,
        metrics_collector=metrics,
        redis_client=redis_client
    )

    # Configure Jobs
    important_jobs = ImportantJobs(
        redis_client=redis_client
    )

    # Get updates from memory and send to users
    telegram_bot.application.job_queue.run_repeating(important_jobs.get_messages_and_send, 60)

    # Reset ngrok message
    telegram_bot.application.job_queue.run_once(important_jobs.sent_ngrok_msg, 5)

    # Reset first sent promo
    telegram_bot.application.job_queue.run_once(important_jobs.reset_default_promo, 7)

    # Kill container in 24 hours (or 86400 seconds)
    telegram_bot.application.job_queue.run_once(
        important_jobs.kill_container, important_jobs.ONE_DAY, name="get_messages_and_send"
    )

    telegram_bot.application.run_polling()


if __name__ == "__main__":
    main()
