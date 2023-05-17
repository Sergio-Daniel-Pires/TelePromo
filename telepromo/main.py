from database import Database
from monitor import Monitoring
from vectorizers import Vectorizers
from telegram_bot import TelegramBot

import asyncio
from threading import Thread

async def verify_urls_price(monitor, current_obj):
    url_list = current_obj['links']
    results = await monitor.prices_from_url(url_list)
    new_prices = monitor.verify_save_prices(results)
    return new_prices

async def continuos_verify_price(db: Database, monitor: Monitoring):
    semaphore = asyncio.Semaphore(4)
    while True:
        await asyncio.sleep(5)
        continue
        tasks = []
        links_cursor = db.get_links()
        for current_obj in links_cursor:
            async with semaphore:
                tasks.append(asyncio.ensure_future(verify_urls_price(monitor, current_obj)))
        results = await asyncio.gather(*tasks)
        print(results) 
        break

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
    #telegram_thread = Thread(target=telegram_bot.run, name="TelegramBot")
    #monitor_thread = Thread(target=asyncio.run, name="Monitor thread", args=(continuos_verify_price(db, monitor),))
    #monitor_thread.start()

    await telegram_bot.iniatilize()
    await continuos_verify_price(db, monitor)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()