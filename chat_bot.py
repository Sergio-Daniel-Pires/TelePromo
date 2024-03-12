import logging

from redis import Redis

from project import config
from project.database import Database
from project.metrics_collector import MetricsCollector
from project.telegram_bot import ImportantJobs, TelegramBot
from project.vectorizers import Vectorizers

logging.getLogger().setLevel(logging.WARNING)
formatter = logging.Formatter('%(asctime)s - %(filename)s - %(levelname)s - %(message)s')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

# Adiciona o handler ao logger raiz
logging.getLogger().addHandler(stream_handler)

def main ():
    metrics = MetricsCollector(9092)

    db = Database(metrics)
    vectorizers = Vectorizers()

    redis_client = Redis(host=config.REDIS_URL, port=6379)

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

    telegram_bot.application.job_queue.run_repeating(
        important_jobs.reset_daily_promos, important_jobs.ONE_DAY
    )


if __name__ == "__main__":
    main()
