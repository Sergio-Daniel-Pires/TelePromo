from project.database import Database
from project.metrics_collector import MetricsCollector
from project.monitor import Monitoring, send_ngrok_message
from project.telegram_bot import TelegramBot
from project.vectorizers import Vectorizers

def main ():
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
        vectorizer=vectorizers,
        metrics_collector=metrics
    )

    telegram_bot.application.job_queue.run_once(
        send_ngrok_message, 2
    )

    telegram_bot.application.job_queue.run_repeating(
      monitor.continuous_verify_price, 60 * 15, first=0
    )

    telegram_bot.application.run_polling()

if __name__ == "__main__":
    main()
