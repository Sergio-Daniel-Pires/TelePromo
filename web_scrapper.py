import asyncio
import logging
import os
import time

from redis import Redis

from project.database import Database
from project.metrics_collector import MetricsCollector
from project.monitor import Monitoring
from project.vectorizers import Vectorizers

logging.getLogger().setLevel(logging.WARNING)

def main ():
    metrics = MetricsCollector(9091)

    db = Database(metrics)
    vectorizers = Vectorizers()

    redis_client = Redis(
        host=os.environ.get('REDIS_URL', 'localhost'), port=6379
    )

    monitor = Monitoring(
        retry=3,
        database=db,
        vectorizer=vectorizers,
        redis_client=redis_client,
        metrics_collector=metrics
    )

    # Start continuos verify prices
    while True:
        current_time = int(time.time())
        elapsed = current_time - monitor.last_execution_time

        if elapsed < monitor.shortest_bot_time:
            logging.warning(
                "Ainda não se passaram "
                f"{int(monitor.shortest_bot_time / 60)} min "
                f"{float(elapsed/60):.1f}"
            )

        else:
            asyncio.run(monitor.continuous_verify_price())
            monitor.last_execution_time = current_time

        time.sleep(10)


if __name__ == "__main__":
    main()
