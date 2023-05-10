from database import Database
from monitor import Monitoring
from vectorizers import Vectorizers
import re
from nltk.util import ngrams

def main():
    db = Database()
    vectorizers = Vectorizers()
    monitor = Monitoring(
        retry = 3,
        database = db,
        vectorizer = vectorizers
    )
    db.new_wish(['computador'], 'eletronic', 'Sergio')
    db.new_wish(['Fone de ouvido'], 'eletronic', 'Walter')
    db.new_wish(['Monitor gamer'], 'eletronic', 'Andreias')
    db.new_wish(['Smartphone samsung'], 'eletronic', 'WalterS')
    links_cursor = db.get_links()
    for current_obj in links_cursor:
        url_list = current_obj['links']
        results = monitor.prices_from_url(url_list)
        monitor.verify_save_prices(results)

if __name__ == "__main__":
    main()